from pyramid.request import Request, RequestLocalCache

from h.security.identity import Identity
from h.security.policy._identity_base import IdentityBasedPolicy


class APIPolicy(IdentityBasedPolicy):
    """The security policy for API requests. Delegates to subpolicies."""

    def __init__(self, sub_policies):
        self.sub_policies = sub_policies
        self._identity_cache = RequestLocalCache(self._load_identity)

    def forget(self, *_args, **_kwargs):
        # forget() isn't supported for stateless API requests.
        return []

    def identity(self, request) -> Identity | None:
        return self._identity_cache.get_or_create(request)

    def remember(self, *_args, **_kwargs):
        # remember() isn't supported for stateless API requests.
        return []

    def _load_identity(self, request: Request) -> Identity | None:
        for policy in applicable_policies(request, self.sub_policies):
            identity = policy.identity(request)
            if identity:
                return identity

        return None


def applicable_policies(request, policies):
    """Return the security policies from `policies` that can handle `request`."""

    return [policy for policy in policies if policy.handles(request)]
