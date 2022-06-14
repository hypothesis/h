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

    def __init__(self, proxy_auth=False):
        """
        Initialise a security policy.

        :param proxy_auth: Replace the default `CookiePolicy` for the UI with
            the `RemoteUserPolicy`.
        """
        self._bearer_token_policy = BearerTokenPolicy()
        self._http_basic_auth_policy = AuthClientPolicy()
        self._identity_cache = RequestLocalCache(self._load_identity)

        self._ui_policy = RemoteUserPolicy() if proxy_auth else CookiePolicy()

    def remember(self, request, userid, **kw):
        """Get the correct headers to remember the given user."""

        self._identity_cache.clear(request)

        return self._call_sub_policies("remember", request, userid, **kw)

    def forget(self, request):
        """Get the correct headers to forget the current login."""

        self._identity_cache.clear(request)

        return self._call_sub_policies("forget", request)

    def identity(self, request) -> Optional[Identity]:
        """
        Get an Identity object for valid credentials.

        :param request: Pyramid request to inspect
        """
        return self._identity_cache.get_or_create(request)

    def _load_identity(self, request):
        return self._call_sub_policies("identity", request)

    def _call_sub_policies(self, method, request, *args, **kwargs):
        """
        Delegate calls to the correct set of security policies.

        :param method: Method to call (like `identity()` or `forget()`)
        :param request: Pyramid request object
        :param args: Args to pass to the method
        :param kwargs: Kwargs to pass to the method
        :return: The response from the correct sub-policy
        """

        if not self._is_api_request(request):
            # This is usually the cookie policy for UI things
            return getattr(self._ui_policy, method)(request, *args, **kwargs)

        # Then we try the bearer header (or `access_token` GET param)
        result = getattr(self._bearer_token_policy, method)(request, *args, **kwargs)

        if not result and self._http_basic_auth_policy.handles(request):
            # Only then do we look for auth clients authenticating with basic
            # HTTP auth credentials
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
