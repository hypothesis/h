from pyramid import interfaces
from pyramid.security import Authenticated
from zope import interface

#: List of route name-method combinations that should
#: allow AuthClient authentication
from h.auth.policy._basic_http_auth import AuthClientPolicy
from h.auth.policy._cookie import CookieAuthenticationPolicy
from h.auth.policy._remote_user import RemoteUserAuthenticationPolicy
from h.auth.policy.bearer_token import TokenAuthenticationPolicy

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
    def __init__(self, proxy_auth=False):
        self._bearer_token_policy = TokenAuthenticationPolicy()
        self._http_basic_auth_policy = AuthClientPolicy()

        if proxy_auth:
            self.ui_policy = RemoteUserAuthenticationPolicy()
        else:
            self.ui_policy = CookieAuthenticationPolicy()

    def authenticated_userid(self, request):
        return self._call_sub_policies("authenticated_userid", request)

    def unauthenticated_userid(self, request):
        return self._call_sub_policies("unauthenticated_userid", request)

    def remember(self, request, userid, **kw):
        return self._call_sub_policies("remember", request, userid, **kw)

    def forget(self, request):
        return self._call_sub_policies("forget", request)

    def effective_principals(self, request):
        if _is_api_request(request):
            user_principals = self._bearer_token_policy.effective_principals(request)
            # If authentication via user_policy was not successful
            if Authenticated not in user_principals and _is_client_request(request):
                return self._http_basic_auth_policy.effective_principals(request)
            return user_principals
        return self.ui_policy.effective_principals(request)

    def _call_sub_policies(self, method, request, *args, **kwargs):
        if _is_api_request(request):
            result = getattr(self._bearer_token_policy, method)(
                request, *args, **kwargs
            )
            if not result and _is_client_request(request):
                return getattr(self._http_basic_auth_policy, method)(
                    request, *args, **kwargs
                )
            return result
        return getattr(self.ui_policy, method)(request, *args, **kwargs)


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
