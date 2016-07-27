# -*- coding: utf-8 -*-

from pyramid import interfaces
from pyramid.authentication import CallbackAuthenticationPolicy
from zope import interface

from h._compat import text_type
from h.auth import tokens


@interface.implementer(interfaces.IAuthenticationPolicy)
class AuthenticationPolicy(object):
    def __init__(self, api_policy, fallback_policy):
        self.api_policy = api_policy
        self.fallback_policy = fallback_policy

    def authenticated_userid(self, request):
        if _is_api_request(request):
            return self.api_policy.authenticated_userid(request)
        return self.fallback_policy.authenticated_userid(request)

    def unauthenticated_userid(self, request):
        if _is_api_request(request):
            return self.api_policy.unauthenticated_userid(request)
        return self.fallback_policy.unauthenticated_userid(request)

    def effective_principals(self, request):
        if _is_api_request(request):
            return self.api_policy.effective_principals(request)
        return self.fallback_policy.effective_principals(request)

    def remember(self, request, userid, **kw):
        if _is_api_request(request):
            return self.api_policy.remember(request, userid, **kw)
        return self.fallback_policy.remember(request, userid, **kw)

    def forget(self, request):
        if _is_api_request(request):
            return self.api_policy.forget(request)
        return self.fallback_policy.forget(request)


@interface.implementer(interfaces.IAuthenticationPolicy)
class TokenAuthenticationPolicy(CallbackAuthenticationPolicy):

    """
    A bearer token authentication policy.

    This is a Pyramid authentication policy in which the user's identity is
    provided by and authenticated by the presence of a valid bearer token in
    the "Authorization" HTTP request header.

    It uses Pyramid's CallbackAuthenticationPolicy to divide responsibility
    between this component (which is responsible only for establishing
    identity), and a callback function, which is responsible for providing
    additional principals for the authenticated user.
    """

    def __init__(self, callback=None, debug=False):
        self.callback = callback
        self.debug = debug

    def remember(self, request, userid, **kw):
        """Not implemented for token auth policy."""
        return []

    def forget(self, request):
        """Not implemented for token auth policy."""
        return []

    def unauthenticated_userid(self, request):
        """
        Return the userid implied by the token in the passed request, if any.

        This function inspects the passed request for bearer tokens, and
        attempts to interpret any found tokens as either API tokens or JWTs,
        in that order.

        :param request: a request object
        :type request: pyramid.request.Request

        :returns: the userid authenticated for the passed request or None
        :rtype: unicode or None
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

        return (tokens.userid_from_api_token(token, request) or
                tokens.userid_from_jwt(token, request))


def _is_api_request(request):
    return (request.path.startswith('/api') and
            request.path not in ['/api/token', '/api/badge'])
