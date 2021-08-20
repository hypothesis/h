from pyramid.interfaces import ISecurityPolicy
from zope.interface import implementer

from h.auth.policy._basic_http_auth import AuthClientPolicy
from h.auth.policy._cookie import CookieAuthenticationPolicy
from h.auth.policy._identity_base import IdentityBasedPolicy
from h.auth.policy._remote_user import RemoteUserAuthenticationPolicy
from h.auth.policy.bearer_token import TokenAuthenticationPolicy


@implementer(ISecurityPolicy)
class AuthenticationPolicy(IdentityBasedPolicy):
    def __init__(self, proxy_auth=False):
        self._bearer_token_policy = TokenAuthenticationPolicy()
        self._http_basic_auth_policy = AuthClientPolicy()

        if proxy_auth:
            self._ui_policy = RemoteUserAuthenticationPolicy()
        else:
            self._ui_policy = CookieAuthenticationPolicy()

    def authenticated_userid(self, request):
        return self._call_sub_policies("authenticated_userid", request)

    def unauthenticated_userid(self, request):
        return self._call_sub_policies("unauthenticated_userid", request)

    def remember(self, request, userid, **kw):
        return self._call_sub_policies("remember", request, userid, **kw)

    def forget(self, request):
        return self._call_sub_policies("forget", request)

    def identity(self, request):
        return self._call_sub_policies("identity", request)

    def _call_sub_policies(self, method, request, *args, **kwargs):
        if not self._is_api_request(request):
            return getattr(self._ui_policy, method)(request, *args, **kwargs)

        result = getattr(self._bearer_token_policy, method)(request, *args, **kwargs)

        if not result and self._http_basic_auth_policy.handles(request):
            return getattr(self._http_basic_auth_policy, method)(
                request, *args, **kwargs
            )

        return result

    @staticmethod
    def _is_api_request(request):
        return request.path.startswith("/api") and request.path not in [
            "/api/token",
            "/api/badge",
        ]
