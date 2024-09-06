from datetime import timedelta

import webob
from pyramid.request import RequestLocalCache
from pyramid.security import Allowed, Denied

from h.security.identity import Identity
from h.security.policy._api import APIPolicy
from h.security.policy._api_cookie import APICookiePolicy
from h.security.policy._auth_client import AuthClientPolicy
from h.security.policy._bearer_token import BearerTokenPolicy
from h.security.policy._cookie import CookiePolicy
from h.security.policy.helpers import AuthTicketCookieHelper, is_api_request

HTML_AUTHCOOKIE_MAX_AGE = int(timedelta(days=365).total_seconds())


class TopLevelPolicy:
    """The top-level security policy. Delegates to subpolicies."""

    def __init__(self):
        self._identity_cache = RequestLocalCache(self._load_identity)

    def forget(self, request, **kw):
        self._identity_cache.clear(request)
        return get_subpolicy(request).forget(request, **kw)

    def identity(self, request) -> Identity | None:
        return self._identity_cache.get_or_create(request)

    def authenticated_userid(self, request):
        return get_subpolicy(request).authenticated_userid(request)

    def remember(self, request, userid, **kw):
        self._identity_cache.clear(request)
        return get_subpolicy(request).remember(request, userid, **kw)

    def permits(self, request, context, permission) -> Allowed | Denied:
        return get_subpolicy(request).permits(request, context, permission)

    def _load_identity(self, request):
        return get_subpolicy(request).identity(request)


@RequestLocalCache()
def get_subpolicy(request):
    """Return the subpolicy for TopLevelSecurityPolicy to delegate to for `request`."""

    # The cookie that's used to authenticate API requests.
    api_authcookie = webob.cookies.SignedCookieProfile(
        secret=request.registry.settings["h_api_auth_cookie_secret"],
        salt=request.registry.settings["h_api_auth_cookie_salt"],
        cookie_name="h_api_authcookie.v2",
        httponly=True,
        secure=request.scheme == "https",
        samesite="strict",
        # Make the API authcookie stay fresh for longer than the HTML one.
        # This is to make it less likely that a browser will have an unexpired HTML
        # authcookie but an expired API one, which can lead to confusing results.
        max_age=HTML_AUTHCOOKIE_MAX_AGE + int(timedelta(hours=1).total_seconds()),
    )
    api_authcookie = api_authcookie.bind(request)

    if is_api_request(request):
        return APIPolicy(
            [
                BearerTokenPolicy(),
                AuthClientPolicy(),
                APICookiePolicy(api_authcookie, AuthTicketCookieHelper()),
            ]
        )

    # The cookie that's used to authenticate HTML page requests.
    html_authcookie = webob.cookies.SignedCookieProfile(
        secret=request.registry.settings["h_auth_cookie_secret"],
        salt="authsanity",
        cookie_name="auth",
        max_age=HTML_AUTHCOOKIE_MAX_AGE,
        httponly=True,
        secure=request.scheme == "https",
    )
    html_authcookie = html_authcookie.bind(request)
    return CookiePolicy(html_authcookie, api_authcookie, AuthTicketCookieHelper())
