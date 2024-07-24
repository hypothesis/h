from pyramid.request import RequestLocalCache

from h.security.identity import Identity
from h.security.policy._api import APIPolicy
from h.security.policy._api_cookie import APICookiePolicy
from h.security.policy._auth_client import AuthClientPolicy
from h.security.policy._cookie import CookiePolicy
from h.security.policy._identity_base import IdentityBasedPolicy
from h.security.policy.bearer_token import BearerTokenPolicy
from h.security.policy.helpers import is_api_request


class TopLevelPolicy(IdentityBasedPolicy):
    """The top-level security policy. Delegates to subpolicies."""

    def __init__(self):
        self._identity_cache = RequestLocalCache(self._load_identity)

    def forget(self, request, **kw):
        self._identity_cache.clear(request)
        return get_subpolicy(request).forget(request, **kw)

    def identity(self, request) -> Identity | None:
        return self._identity_cache.get_or_create(request)

    def remember(self, request, userid, **kw):
        self._identity_cache.clear(request)
        return get_subpolicy(request).remember(request, userid, **kw)

    def _load_identity(self, request):
        return get_subpolicy(request).identity(request)


@RequestLocalCache()
def get_subpolicy(request):
    """Return the subpolicy for TopLevelSecurityPolicy to delegate to for `request`."""
    if is_api_request(request):
        return APIPolicy(
            [BearerTokenPolicy(), AuthClientPolicy(), APICookiePolicy(CookiePolicy())]
        )

    return CookiePolicy()
