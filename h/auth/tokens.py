# -*- coding: utf-8 -*-

import datetime

import jwt
from zope.interface import implementer

from h._compat import text_type
from h.auth import models
from h.auth.interfaces import IAuthenticationToken


@implementer(IAuthenticationToken)
class LegacyClientJWT(object):

    """
    A wrapper around JWT issued to the Hypothesis client.

    Exposes the standard "auth token" interface on top of legacy tokens.
    """

    def __init__(self, body, key, audience=None, leeway=240):
        self.payload = jwt.decode(body,
                                  key=key,
                                  audience=audience,
                                  leeway=leeway,
                                  algorithms=['HS256'])

    @property
    def userid(self):
        return self.payload.get('sub')


def generate_jwt(request, expires_in):
    """Return a signed JSON Web Token for the given request.

    The token can be used in the Authorization header in subsequent requests to
    the API to authenticate the user identified by the
    request.authenticated_userid of the _current_ request.

    :param request: the HTTP request to return a token for, the token will
        authenticate the userid given by this request's authenticated_userid
        property
    :type request: pyramid.request.Request

    :param expires_in: when the returned token should expire, in seconds from
        the current time
    :type expires_in: int

    :returns: a signed JSON Web Token
    :rtype: string

    """
    now = datetime.datetime.utcnow().replace(microsecond=0)

    claims = {
        'iss': request.registry.settings['h.client_id'],
        'aud': request.host_url,
        'sub': request.authenticated_userid,
        'exp': now + datetime.timedelta(seconds=expires_in),
        'iat': now,
    }

    return jwt.encode(claims,
                      request.registry.settings['h.client_secret'],
                      algorithm='HS256')


def auth_token(request):
    """
    Fetch the token (if any) associated with a request.

    :param request: the request object
    :type request: pyramid.request.Request

    :returns: the auth token carried by the request, or None
    :rtype: h.auth.models.Token or None
    """
    try:
        header = request.headers['Authorization']
    except KeyError:
        return None

    if not header.startswith('Bearer '):
        return None

    token = text_type(header[len('Bearer '):]).strip()
    # If the token is empty at this point, it is clearly invalid and we
    # should reject it.
    if not token:
        return None

    api_token = (request.db.query(models.Token)
                 .filter_by(value=token)
                 .one_or_none())
    if api_token is not None:
        return api_token

    # If we've got this far it's possible the token is a legacy client JWT.
    return _maybe_jwt(token, request)


def _maybe_jwt(token, request):
    try:
        return LegacyClientJWT(token,
                               key=request.registry.settings['h.client_secret'],
                               audience=request.host_url)
    except jwt.InvalidTokenError:
        return None
