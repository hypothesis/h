from pyramid.csrf import check_csrf_origin, check_csrf_token
from pyramid.request import Request
from webob.cookies import SignedCookieProfile

from h.security.identity import Identity
from h.security.policy.helpers import AuthTicketCookieHelper

COOKIE_AUTHENTICATABLE_API_REQUESTS = [
    ("api.groups", "POST"),  # Create a new group.
    ("api.group", "PATCH"),  # Edit an existing group.
]


class APICookiePolicy:
    """Authenticate API requests with cookies."""

    def __init__(self, cookie: SignedCookieProfile, helper: AuthTicketCookieHelper):
        self.cookie = cookie
        self.helper = helper

    @staticmethod
    def handles(request: Request) -> bool:
        """Return True if this policy applies to `request`."""
        return (
            request.matched_route.name,
            request.method,
        ) in COOKIE_AUTHENTICATABLE_API_REQUESTS

    def identity(self, request: Request) -> Identity | None:
        identity, _ = self.helper.identity(self.cookie, request)

        if identity is None:
            return identity

        # Require cookie-authenticated API requests to also have a valid CSRF
        # token.
        #
        # This offers defense-in-depth: if our cookie authentication fails
        # (e.g. because of a security bug in our code) this additional CSRF
        # check might save us.
        #
        # This also secures some situations that even a SameSite=Strict cookie
        # cannot: browsers send cookies on all requests that the cookie applies
        # to, not only requests triggered by JavaScript calls. We allow
        # user-generated content on the site and malicious user content could
        # include links that, when clicked by a victom user, cause the browser
        # to make API requests that include auth cookies.
        check_csrf_origin(request)
        check_csrf_token(request)

        self.helper.add_vary_by_cookie(request)

        return identity
