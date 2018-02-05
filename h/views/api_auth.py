# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging

from oauthlib.oauth2 import OAuth2Error
from pyramid import security
from pyramid.httpexceptions import HTTPFound, exception_response
from pyramid.view import view_config, view_defaults

from h import models
from h._compat import urlparse
from h.exceptions import OAuthTokenError
from h.services.oauth_validator import DEFAULT_SCOPES
from h.util.datetime import utc_iso8601
from h.views.api_config import api_config

log = logging.getLogger(__name__)


@view_defaults(route_name='oauth_authorize')
class OAuthAuthorizeController(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.user_svc = self.request.find_service(name='user')
        self.oauth = self.request.find_service(name='oauth_provider')

    @view_config(request_method='GET',
                 renderer='h:templates/oauth/authorize.html.jinja2')
    def get(self):
        """
        Validate the OAuth authorization request.

        If the authorization request is valid and the client is untrusted,
        this will render an authorization page allowing the user to
        accept or decline the request.

        If the authorization request is valid and the client is trusted,
        this will skip the users' confirmation and create an authorization
        code and deliver it to the client application.
        """
        return self._authorize()

    @view_config(request_method='GET',
                 request_param='response_mode=web_message',
                 renderer='h:templates/oauth/authorize.html.jinja2')
    def get_web_message(self):
        """
        Validate the OAuth authorization request for response mode ``web_response``.

        This is doing the same as ``get``, but it will deliver the
        authorization code (if the client is trusted) as a ``web_response``.
        More information about ``web_response`` is in draft-sakimura-oauth_.

        .. _draft-sakimura-oauth: https://tools.ietf.org/html/draft-sakimura-oauth-wmrm-00
        """
        response = self._authorize()

        if isinstance(response, HTTPFound):
            self.request.override_renderer = 'h:templates/oauth/authorize_web_message.html.jinja2'
            return self._render_web_message_response(response.location)

        return response

    @view_config(request_method='POST',
                 effective_principals=security.Authenticated,
                 renderer='json')
    def post(self):
        """
        Create an OAuth authorization code.

        This validates the request and creates an OAuth authorization code
        for the authenticated user, it then returns this to the client.
        """
        return self._authorized_response()

    @view_config(request_method='POST',
                 request_param='response_mode=web_message',
                 effective_principals=security.Authenticated,
                 renderer='h:templates/oauth/authorize_web_message.html.jinja2')
    def post_web_message(self):
        """
        Create an OAuth authorization code.

        This is doing the same as ``post``, but it will deliver the
        authorization code as a ``web_response``.
        More information about ``web_response`` is in draft-sakimura-oauth_.

        .. _draft-sakimura-oauth: https://tools.ietf.org/html/draft-sakimura-oauth-wmrm-00
        """
        found = self._authorized_response()
        return self._render_web_message_response(found.location)

    @view_config(context=OAuth2Error,
                 renderer='h:templates/oauth/error.html.jinja2')
    def error(self):
        description = self.context.description
        if not self.context.description:
            description = 'Error: {}'.format(self.context.error)
        return {'description': description}

    def _authorize(self):
        scopes, credentials = self.oauth.validate_authorization_request(self.request.url)

        if self.request.authenticated_userid is None:
            raise HTTPFound(self.request.route_url('login', _query={
                              'next': self.request.url,
                              'for_oauth': True}))

        client_id = credentials.get('client_id')
        client = self.request.db.query(models.AuthClient).get(client_id)

        # If the client is "trusted" -- which means its code is
        # owned/controlled by us -- then we don't ask the user to explicitly
        # authorize it. It is assumed to be authorized to act on behalf of the
        # logged-in user.
        if client.trusted:
            return self._authorized_response()

        state = credentials.get('state')
        user = self.user_svc.fetch(self.request.authenticated_userid)
        response_mode = credentials.get('request').response_mode

        return {'username': user.username,
                'client_name': client.name,
                'client_id': client.id,
                'response_mode': response_mode,
                'response_type': client.response_type.value,
                'state': state}

    def _authorized_response(self):
        # We don't support scopes at the moment, but oauthlib does need a scope,
        # so we're explicitly overwriting whatever the client provides.
        scopes = DEFAULT_SCOPES
        user = self.user_svc.fetch(self.request.authenticated_userid)
        credentials = {'user': user}

        headers, _, status = self.oauth.create_authorization_response(
                self.request.url, scopes=scopes, credentials=credentials)

        try:
            return HTTPFound(location=headers['Location'])
        except KeyError:
            client_id = self.request.params.get('client_id')
            raise RuntimeError('created authorisation code for client "{}" but got no redirect location'.format(client_id))

    def _render_web_message_response(self, redirect_uri):
        location = urlparse.urlparse(redirect_uri)
        params = urlparse.parse_qs(location.query)
        origin = '{url.scheme}://{url.netloc}'.format(url=location)

        state = None
        states = params.get('state', [])
        if states:
            state = states[0]

        return {
            'code': params.get('code', [])[0],
            'origin': origin,
            'state': state,
        }


class OAuthAccessTokenController(object):
    def __init__(self, request):
        self.request = request

        self.oauth = self.request.find_service(name='oauth_provider')

    @api_config(route_name='token', request_method='POST')
    def post(self):
        headers, body, status = self.oauth.create_token_response(
            self.request.url, self.request.method, self.request.POST, self.request.headers)
        if status == 200:
            return json.loads(body)
        else:
            raise exception_response(status, body=body)


class OAuthRevocationController(object):
    def __init__(self, request):
        self.request = request

        self.oauth = self.request.find_service(name='oauth_provider')

    @api_config(route_name='oauth_revoke', request_method='POST')
    def post(self):
        headers, body, status = self.oauth.create_revocation_response(
            self.request.url, self.request.method, self.request.POST, self.request.headers)
        if status == 200:
            return {}
        else:
            raise exception_response(status, body=body)


@api_config(route_name='api.debug_token', request_method='GET')
def debug_token(request):
    if not request.auth_token:
        raise OAuthTokenError('Bearer token is missing in Authorization HTTP header',
                              'missing_token',
                              401)

    svc = request.find_service(name='auth_token')
    token = svc.validate(request.auth_token)
    if token is None:
        raise OAuthTokenError('Bearer token does not exist or is expired',
                              'missing_token',
                              401)

    token = svc.fetch(request.auth_token)
    return _present_debug_token(token)


@api_config(context=OAuthTokenError,
            # This is a handler called only if a request fails, so the CORS
            # preflight request will have been handled by the original view.
            enable_preflight=False)
def api_token_error(context, request):
    """Handle an expected/deliberately thrown API exception."""
    request.response.status_code = context.status_code
    resp = {'error': context.type}
    if context.message:
        resp['error_description'] = context.message
    return resp


def _present_debug_token(token):
    data = {'userid': token.userid,
            'expires_at': utc_iso8601(token.expires) if token.expires else None,
            'issued_at': utc_iso8601(token.created),
            'expired': token.expired}

    if token.authclient:
        data['client'] = {'id': token.authclient.id,
                          'name': token.authclient.name}

    return data
