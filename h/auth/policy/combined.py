from pyramid.interfaces import ISecurityPolicy
from zope.interface import implementer

from h.auth.policy._basic_http_auth import AuthClientPolicy
from h.auth.policy._cookie import CookiePolicy
from h.auth.policy._identity_base import IdentityBasedPolicy
from h.auth.policy._remote_user import RemoteUserPolicy
from h.auth.policy.bearer_token import TokenPolicy


@implementer(ISecurityPolicy)
class SecurityPolicy(IdentityBasedPolicy):
    def __init__(self, proxy_auth=False):
        self._bearer_token_policy = TokenPolicy()
        self._http_basic_auth_policy = AuthClientPolicy()

        self._ui_policy = RemoteUserPolicy() if proxy_auth else CookiePolicy()

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
