from typing import Optional

from pyramid.interfaces import ISecurityPolicy
from pyramid.request import RequestLocalCache
from zope.interface import implementer

from h.security.identity import Identity
from h.security.policy._basic_http_auth import AuthClientPolicy
from h.security.policy._cookie import CookiePolicy
from h.security.policy._identity_base import IdentityBasedPolicy
from h.security.policy._remote_user import RemoteUserPolicy
from h.security.policy.bearer_token import BearerTokenPolicy


@implementer(ISecurityPolicy)
class SecurityPolicy(IdentityBasedPolicy):
    """
    The security policy for `h`.

    This delegates to various different policies depending on the situation.
    """

    def __init__(self):
        self._identity_cache = RequestLocalCache(self._load_identity)

    def remember(self, request, userid, **kw):
        """Get the correct headers to remember the given user."""

        self._identity_cache.clear(request)

        return call_policies("remember", [], request, userid, **kw)

    def forget(self, request, **kw):
        """Get the correct headers to forget the current login."""

        self._identity_cache.clear(request)

        return call_policies("forget", [], request, **kw)

    def identity(self, request) -> Optional[Identity]:
        """
        Get an Identity object for valid credentials.

        :param request: Pyramid request to inspect
        """
        return self._identity_cache.get_or_create(request)

    def _load_identity(self, request):
        return call_policies("identity", None, request)


def call_policies(method: str, fallback, request, *args, **kwargs):
    """
    Call `method` on each applicable security policy and return the first result.

    Call `method` on each security policy that is applicable to `request` in
    turn and return the result from the first policy that returns a truthy value.

    If no security policies are applicable to `request` or if no applicable
    policy returns a truthy value, return `fallback`.
    """
    policies = [RemoteUserPolicy, CookiePolicy, BearerTokenPolicy, AuthClientPolicy]

    for policy in applicable_policies(request, policies):
        result = getattr(policy(), method)(request, *args, **kwargs)
        if result:
            return result

    return fallback


def applicable_policies(request, policies):
    """Return the security policies from `policies` that can handle `request`."""

    return [policy for policy in policies if policy.handles(request)]
