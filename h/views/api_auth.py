# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.view import view_config, view_defaults
from pyramid import security

from h.exceptions import OAuthTokenError
from h.util.view import cors_json_view
from h.util.datetime import utc_iso8601


@view_defaults(route_name='oauth_authorize')
class OAuthAuthorizeController(object):

    def __init__(self, request):
        self.request = request
        self.oauth_svc = self.request.find_service(name='oauth')
        self.user_svc = self.request.find_service(name='user')

    @view_config(request_method='GET',
                 renderer='h:templates/oauth/authorize.html.jinja2')
    def get(self):
        """
        Check the user's authentication status and present the authorization
        page.
        """
        self._check_params()

        if self.request.authenticated_userid is None:
            raise HTTPFound(self.request.route_url('login', _query={
                              'next': self.request.url}))

        params = self.request.params
        user = self.user_svc.fetch(self.request.authenticated_userid)

        return {'username': user.username,
                'client_name': 'Hypothesis',
                'client_id': params['client_id'],
                'response_type': params['response_type'],
                'response_mode': params['response_mode'],
                'state': params.get('state')}

    @view_config(request_method='POST',
                 renderer='h:templates/oauth/post_authorize.html.jinja2',
                 effective_principals=security.Authenticated)
    def post(self):
        """
        Process an authentication request and return an auth code to the client.

        Depending on the "response_mode" parameter the auth code will be
        delivered either via a redirect or via a `postMessage` call to the
        opening window.
        """
        authclient = self._check_params()

        user = self.user_svc.fetch(self.request.authenticated_userid)

        # Create an "authorization code" for the response.
        # This is in fact just a JWT grant token since auth codes have not yet
        # been implemented.
        auth_code = self.oauth_svc.create_grant_token(user, authclient)

        params = self.request.params

        return {'code': auth_code,
                # Once authclients have an Origin property, that should be used
                # instead here.
                'origin': self.request.host_url,
                'state': params.get('state')}

    def _check_params(self):
        """
        Check parameters for the authorization request.

        If the parameters are valid, returns an authclient.
        Otherwise, raises an exception.
        """
        params = self.request.params

        client_id = params.get('client_id', '')
        authclient = self.oauth_svc.get_authclient_by_id(client_id)
        if not authclient:
            raise HTTPBadRequest('Unknown client ID "{}"'.format(client_id))

        if authclient.authority != self.request.authority:
            raise HTTPBadRequest('Client "{}" not allowed to authorize "{}" users'.format(
                                 client_id, self.request.authority))

        response_type = params.get('response_type')
        if response_type != 'code':
            raise HTTPBadRequest('Unsupported response type "{}"'
                                 .format(response_type))

        response_mode = params.get('response_mode', 'query')
        if response_mode != 'web_message':
            raise HTTPBadRequest('Unsupported response mode "{}"'.format(response_mode))

        return authclient


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
