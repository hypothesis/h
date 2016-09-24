# -*- coding: utf-8 -*-

from pyramid import interfaces
from pyramid.authentication import CallbackAuthenticationPolicy
from zope import interface


@interface.implementer(interfaces.IAuthenticationPolicy)
class AuthenticationPolicy(object):
    def __init__(self, api_policy, fallback_policy, migration_policy=None):
        self.api_policy = api_policy
        self.fallback_policy = fallback_policy
        self.migration_policy = migration_policy

    def authenticated_userid(self, request):
        if _is_api_request(request):
            return self.api_policy.authenticated_userid(request)

        userid = self.fallback_policy.authenticated_userid(request)
        if userid is not None:
            return userid

        # In case we couldn't authenticate the user against the fallback policy
        # and we're in the process of migrating from one policy to another,
        # then we check if we can authenticate against the deprecated
        # migration policy. If that succeeded, then we remember the user in the
        # fallback policy and from then on this code path will not be called
        # anymore.
        if self.migration_policy is None:
            return userid

        userid = self.migration_policy.authenticated_userid(request)
        if userid is not None:
            headers = self.fallback_policy.remember(request, userid)
            request.response.headers.extend(headers)

        return userid

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
    provided by and authenticated by the presence of a valid authentication
    token associated with the request. The token is retrieved from the
    ``request.auth_token`` property, which is provided by the
    :py:func:`h.auth.token.auth_token` function.

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

        :param request: a request object
        :type request: pyramid.request.Request

        :returns: the userid authenticated for the passed request or None
        :rtype: unicode or None
        """
        token = getattr(request, 'auth_token', None)
        if token is None or not token.is_valid():
            return None

        return token.userid


def _is_api_request(request):
    return (request.path.startswith('/api') and
            request.path not in ['/api/token', '/api/badge'])
