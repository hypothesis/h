# -*- coding: utf-8 -*-

import datetime

import jwt
from zope.interface import implementer

from h._compat import text_type
from h import models
from h.auth.interfaces import IAuthenticationToken


@implementer(IAuthenticationToken)
class Token(object):
    """
    A long-lived API token for a user.

    This is a wrapper class that wraps an ``h.models.Token`` and provides an
    implementation of the ``IAuthenticationToken`` interface.

    Unlike ``models.Token`` this class is not a sqlalchemy ORM class so it can
    be used after the request's db session has been committed or invalidated
    without getting ``DetachedInstanceError``s from sqlalchemy.

    """

    def __init__(self, token_model):
        self.expires = token_model.expires
        self.userid = token_model.userid

    def is_valid(self):
        """Return ``True`` if this token is not expired, ``False`` if it is."""
        if self.expires is None:
            return True
        now = datetime.datetime.utcnow()
        return now < self.expires


@implementer(IAuthenticationToken)
class LegacyClientJWT(object):

    """
    A wrapper around JWT issued to the Hypothesis client.

    Exposes the standard "auth token" interface on top of legacy tokens.
    """

    def __init__(self, body, key, leeway=240):
        self.payload = jwt.decode(body,
                                  key=key,
                                  leeway=leeway,
                                  algorithms=['HS256'])

    def is_valid(self):
        """Check if the token is valid. Always true for JWTs."""
        # JWT validity checks happen at construction time. If an instance is
        # successfully constructed, it is by definition valid.
        return True

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
        'sub': request.authenticated_userid,
        'exp': now + datetime.timedelta(seconds=expires_in),
        'iat': now,
    }

    return jwt.encode(claims,
                      request.registry.settings['h.client_secret'],
                      algorithm='HS256')


class AuthTokenFetcher(object):
    """
    Fetch the token (if any) associated with a request.

    This looks for the a bearer token in the "Authorization" header. This method
    can optionally look for the token in the GET URL parameters by providing a
    key as the ``get_param`` argument.

    :returns: the auth token carried by the request, or None
    :rtype: h.models.Token or None
    """
    def __init__(self, request):
        self.request = request
        self._cache = {}

    def __call__(self, get_param=None):
        """
        Returns the token.

        :param get_param: the GET URI parameter key
        :type unicode

        :returns: the auth token carried by the request, or None
        :rtype: h.auth.tokens.Token or None
        """
        cache_key = 'default'
        if get_param is not None:
            cache_key = 'param-%s' % get_param

        if cache_key not in self._cache:
            self._cache[cache_key] = self._fetch(get_param)

        return self._cache[cache_key]

    def _fetch(self, get_param):
        token = None

        if get_param is None:
            token = _header_token(self.request)
        else:
            token = self.request.GET.get(get_param, None)

        if not token:
            return None

        token_model = (self.request.db.query(models.Token)
                       .filter_by(value=token)
                       .one_or_none())
        if token_model is not None:
            return Token(token_model)

        # If we've got this far it's possible the token is a legacy client JWT.
        return _maybe_jwt(token, self.request)


def _maybe_jwt(token, request):
    try:
        return LegacyClientJWT(token,
                               key=request.registry.settings['h.client_secret'])
    except jwt.InvalidTokenError:
        return None


def _header_token(request):
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

    return token
