# -*- coding: utf-8 -*-

import datetime

import jwt
from pyramid import exceptions
from pyramid import security
from pyramid import session


def translate_annotation_principals(principals):
    """
    Translate a list of annotation principals to a list of pyramid principals.
    """
    result = set([])
    for principal in principals:
        # Ignore suspicious principals from annotations
        if principal.startswith('system.'):
            continue
        if principal == 'group:__world__':
            result.add(security.Everyone)
        elif principal == 'group:__authenticated__':
            result.add(security.Authenticated)
        else:
            result.add(principal)
    return list(result)


def check_csrf_token(request):
    """Return True if the request has a valid CSRF token, False otherwise."""
    try:
        session.check_csrf_token(request, token='assertion')
    except exceptions.BadCSRFToken:
        return False
    return True


def generate_signed_token(request):
    """Generate a signed JSON Web Token from OAuth attributes of the request.

    A JSON Web Token [jwt]_ is a token that contains a header, describing the
    algorithm used for signing, a set of claims (the payload), and a trailing
    signature.

    .. [jwt] https://tools.ietf.org/html/draft-ietf-oauth-json-web-token
    """
    now = datetime.datetime.utcnow().replace(microsecond=0)
    ttl = datetime.timedelta(seconds=request.expires_in)

    claims = {
        'iss': request.registry.settings['h.client_id'],
        'aud': request.host_url,
        'sub': request.authenticated_userid,
        'exp': now + ttl,
        'iat': now,
    }

    return jwt.encode(claims, request.registry.settings['h.client_secret'])
