# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyramid import interfaces
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authentication import CallbackAuthenticationPolicy
from zope import interface


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
class AuthClientPolicy(BasicAuthAuthenticationPolicy):

    """
    An authentication policy for registered auth_clients.
    """

    def __init__(self, check, realm='Realm', debug=False):
        self.check = check
        self.realm = realm
        self.debug = debug

    def authenticated_userid(self, request):
        """
        Currently the behavior here is different than other Auth policies
        as the net result is that, although Authentication may well be
        successful, we don't end up with an authenticated ``userid``.

        Thus, ``request.authenticated_userid`` will be None and
        ```request.user`` will not be set (see :py:mod:`h.accounts`)

        However, the request will be authenticated. In a view,
        ``effective_principals=security.Authenticated`` would be satisfied.

        .. todo::

           Extend me here (carefully) to operate on behalf of user in authority)
        """
        return None


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
        token_str = None
        if _is_ws_request(request):
            token_str = request.GET.get('access_token', None)
        if token_str is None:
            token_str = getattr(request, 'auth_token', None)

        if token_str is None:
            return None

        svc = request.find_service(name='auth_token')
        token = svc.validate(token_str)
        if token is None:
            return None

        return token.userid


def _is_api_request(request):
    return (request.path.startswith('/api') and
            request.path not in ['/api/token', '/api/badge'])


def _is_ws_request(request):
    return request.path == '/ws'
