# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

from oauthlib.oauth2 import (
    InvalidRequestError,
    InvalidRequestFatalError,
    WebApplicationServer,
)
from pyramid import security
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults

from h import models
from h.exceptions import OAuthTokenError
from h.services.oauth_validator import DEFAULT_SCOPES
from h.util.datetime import utc_iso8601
from h.util.view import cors_json_view

log = logging.getLogger(__name__)


@view_defaults(route_name='oauth_authorize')
class OAuthAuthorizeController(object):
    def __init__(self, request):
        self.request = request
        self.user_svc = self.request.find_service(name='user')

        validator = self.request.find_service(name='oauth_validator')
        self.oauth = WebApplicationServer(validator)

    @view_config(request_method='GET',
                 renderer='h:templates/oauth/authorize.html.jinja2')
    def get(self):
        scopes, credentials = self.oauth.validate_authorization_request(self.request.url)

        if self.request.authenticated_userid is None:
            raise HTTPFound(self.request.route_url('login', _query={
                              'next': self.request.url}))

        client_id = credentials.get('client_id')
        state = credentials.get('state')

        user = self.user_svc.fetch(self.request.authenticated_userid)
        client = self.request.db.query(models.AuthClient).get(client_id)

        return {'username': user.username,
                'client_name': client.name,
                'client_id': client.id,
                'response_type': client.response_type.value,
                'state': state}

    @view_config(request_method='POST',
                 effective_principals=security.Authenticated)
    def post(self):
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


@view_defaults(renderer='h:templates/oauth/error.html.jinja2')
class OAuthAuthorizeErrorController(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(context=InvalidRequestFatalError)
    @view_config(context=InvalidRequestError)
    def invalid_authorize_request(self):
        return {'description': self.context.description}


@cors_json_view(route_name='token', request_method='POST')
def access_token(request):
    svc = request.find_service(name='oauth')

    user, authclient = svc.verify_token_request(request.POST)
    token = svc.create_token(user, authclient)

    response = {
        'access_token': token.value,
        'token_type': 'bearer',
    }

    if token.expires:
        response['expires_in'] = token.ttl

    if token.refresh_token:
        response['refresh_token'] = token.refresh_token

    return response


@cors_json_view(route_name='api.debug_token', request_method='GET')
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


@cors_json_view(context=OAuthTokenError)
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
