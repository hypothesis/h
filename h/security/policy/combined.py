from pyramid.interfaces import ISecurityPolicy
from pyramid.request import RequestLocalCache
from zope.interface import implementer

from h.security.policy._basic_http_auth import AuthClientPolicy
from h.security.policy._cookie import CookiePolicy
from h.security.policy._identity_base import IdentityBasedPolicy
from h.security.policy._remote_user import RemoteUserPolicy
from h.security.policy.bearer_token import TokenPolicy


@implementer(ISecurityPolicy)
class SecurityPolicy(IdentityBasedPolicy):
    def __init__(self, proxy_auth=False):
        self._bearer_token_policy = TokenPolicy()
        self._http_basic_auth_policy = AuthClientPolicy()
        self._identity_cache = RequestLocalCache(self._load_identity)

        self._ui_policy = RemoteUserPolicy() if proxy_auth else CookiePolicy()

    def remember(self, request, userid, **kw):
        self._identity_cache.clear(request)

        return self._call_sub_policies("remember", request, userid, **kw)

    def forget(self, request):
        self._identity_cache.clear(request)

        return self._call_sub_policies("forget", request)

    def identity(self, request):
        return self._identity_cache.get_or_create(request)

    def _load_identity(self, request):
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
