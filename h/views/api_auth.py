# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.auth.services import TOKEN_TTL
from h.exceptions import OAuthTokenError
from h.util.view import json_view


@json_view(route_name='token', request_method='POST')
def access_token(request):
    svc = request.find_service(name='oauth')

    user = svc.verify_jwt_bearer(
        assertion=request.POST.get('assertion'),
        grant_type=request.POST.get('grant_type'))
    token = svc.create_token(user)

    return {
        'access_token': token.value,
        'token_type': 'bearer',
        'expires_in': TOKEN_TTL.total_seconds(),
    }


@json_view(context=OAuthTokenError)
def api_token_error(context, request):
    """Handle an expected/deliberately thrown API exception."""
    request.response.status_code = context.status_code
    resp = {'error': context.type}
    if context.message:
        resp['error_description'] = context.message
    return resp
