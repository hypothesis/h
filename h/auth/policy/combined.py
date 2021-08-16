from pyramid import interfaces
from pyramid.security import Authenticated
from zope import interface

#: List of route name-method combinations that should
#: allow AuthClient authentication
AUTH_CLIENT_API_WHITELIST = [
    ("api.groups", "POST"),
    ("api.group", "PATCH"),
    ("api.group", "GET"),
    ("api.group_upsert", "PUT"),
    ("api.group_member", "POST"),
    ("api.users", "POST"),
    ("api.user_read", "GET"),
    ("api.user", "PATCH"),
    ("api.bulk", "POST"),
]


@interface.implementer(interfaces.IAuthenticationPolicy)
class AuthenticationPolicy:
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
class APIAuthenticationPolicy:
    """
    An authentication policy for Hypothesis API endpoints.

    Two types of authentication apply to Hypothesis API endpoints:

    * Authentication for a single user using Token authentication
    * Authentication for an auth_client, either as the client itself or
      "on behalf of" a user within that client's authority

    This policy delegates to :py:class:`~h.auth.TokenAuthenticationPolicy` and
    :py:class:`~h.auth.AuthClientPolicy`, always preferring Token when available

    Initially, the ``client_policy`` will only be used to authenticate requests
    that correspond to certain endpoint services.
    """

    def __init__(self, user_policy, client_policy):
        self._user_policy = user_policy
        self._client_policy = client_policy

    def authenticated_userid(self, request):
        user_authid = self._user_policy.authenticated_userid(request)
        if user_authid is None and _is_client_request(request):
            return self._client_policy.authenticated_userid(request)
        return user_authid

    def unauthenticated_userid(self, request):
        user_unauth_id = self._user_policy.unauthenticated_userid(request)
        if user_unauth_id is None and _is_client_request(request):
            return self._client_policy.unauthenticated_userid(request)
        return user_unauth_id

    def effective_principals(self, request):
        """
        Return the request's effective principals.

        The ``effective_principals`` method of classes that implement
        Pyramid's Authentication Interface always returns at least one principal:
        :py:attr:`pyramid.security.Everyone`

        The absence of :py:attr:`pyramid.security.Authenticated` in returned
        principals means that authentication was not successful on this request
        using the given policy.

        :rtype: list Containing at minimum :py:attr:`pyramid.security.Everyone`
        """
        user_principals = self._user_policy.effective_principals(request)
        # If authentication via user_policy was not successful
        if Authenticated not in user_principals and _is_client_request(request):
            return self._client_policy.effective_principals(request)
        return user_principals

    def remember(self, request, userid, **kw):
        remembered = self._user_policy.remember(request, userid, **kw)
        if remembered == [] and _is_client_request(request):
            return self._client_policy.remember(request, userid, **kw)
        return remembered

    def forget(self, request):
        forgot = self._user_policy.forget(request)
        if forgot == [] and _is_client_request(request):
            return self._client_policy.forget(request)
        return forgot


def _is_api_request(request):
    return request.path.startswith("/api") and request.path not in [
        "/api/token",
        "/api/badge",
    ]


def _is_client_request(request):
    """
    Return if this is auth_client_auth authentication valid for the given request.

    Uuthentication should be performed by
    :py:class:`~h.auth.policy.AuthClientPolicy` only for requests
    that match the whitelist.

    The whitelist will likely evolve.

    :rtype: bool
    """
    if request.matched_route:
        return (request.matched_route.name, request.method) in AUTH_CLIENT_API_WHITELIST
    return False
