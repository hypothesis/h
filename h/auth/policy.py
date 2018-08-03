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
class AuthClientPolicy(object):

    """
    An authentication policy for registered auth_clients

    Authentication for a request to API routes with HTTP Basic Authentication
    credentials that represent a registered AuthClient with client_credentials
    in the db.

    Authentication can be of two types:

    * The client itself. Some endpoints allow an authenticated auth_client to
      take action on users within its authority, such as creating a user or
      adding a user to a group. In this case, assuming credentials are valid,
      the request will be authenticated, but no ``authenticated_userid`` (and
      thus no request.user) will be set
    * A user within the client's associated authority. If an HTTP
      `X-Forwarded-User` header is present, its value will be treated as a
      ``userid`` and, if the client credentials are valid _and_ the userid
      represents an extant user within the client's authority, the request
      will be authenticated as that user. In this case, ``authenticated_userid``
      will be set and there will ultimately be a request.user available.

    Note: To differentiate between request with a Token-authenticated user and
    a request with an auth_client forwarded user, the latter has an additional
    principal, ``client:{client_id}@{authority}`` to mark it as being authenticated
    on behalf of an auth_client
    """

    def __init__(self, check):
        """
        :param: check A callback function that accepts (username, password, request)
                and should return a list of principals or `None` if auth
                unsucessful; it will be called with the username and password
                parsed from the Authentication header
        """
        self.basic_auth_policy = BasicAuthAuthenticationPolicy(check=check)
        self.check = check

    def unauthenticated_userid(self, request):
        """
        Return the forwarded userid or the client_id

        If a forwarded user header is set, return the ``userid`` (its value)
        Otherwise return the username parsed from the Basic Auth header

        :rtype: str
        """
        proxy_userid = AuthClientPolicy.forwarded_userid(request)
        if proxy_userid is not None:
            return proxy_userid

        # username from BasicAuth header
        return self.basic_auth_policy.unauthenticated_userid(request)

    def authenticated_userid(self, request):
        """
        Return any forwarded userid or None

        Rely mostly on ``Pyramid.authentication.BasicAuthAuthenticationPolicy``'s
        authenticated_userid, but don't
        actually return a userid unless there is a forwarded user (the auth
        client itself is not a "user")

        :rtype: `~h.models.user.User.userid` or None
        """
        forwarded_userid = AuthClientPolicy.forwarded_userid(request)

        if forwarded_userid is None:  # only set authenticated_userid if forwarded user
            return None

        # username extracted from BasicAuth header
        auth_userid = self.basic_auth_policy.unauthenticated_userid(request)

        # authentication of BasicAuth and forwarded user
        callback_ok = self.basic_auth_policy.callback(auth_userid, request)

        if callback_ok is not None:
            return forwarded_userid  # This should always be a userid, not an auth_client id

    def effective_principals(self, request):
        """Delegate this to BasicAuthAuthenticationPolicy"""
        return self.basic_auth_policy.effective_principals(request)

    def remember(self, request, userid, **kw):
        """Not implemented for basic auth client policy."""
        return []

    def forget(self, request):
        """Not implemented for basic auth client policy."""
        return []

    @classmethod
    def forwarded_userid(cls, request):
        """Look in header for userid"""
        return request.headers.get('X-Forwarded-User', None)


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
