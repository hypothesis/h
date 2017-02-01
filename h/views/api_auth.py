# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.exceptions import OAuthTokenError
from h.util.view import cors_json_view


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


@cors_json_view(context=OAuthTokenError)
def api_token_error(context, request):
    """Handle an expected/deliberately thrown API exception."""
    request.response.status_code = context.status_code
    resp = {'error': context.type}
    if context.message:
        resp['error_description'] = context.message
    return resp
