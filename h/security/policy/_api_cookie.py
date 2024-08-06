from pyramid.request import Request
from pyramid.security import Allowed, Denied
from webob.cookies import SignedCookieProfile

from h.security.identity import Identity
from h.security.permits import identity_permits
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
        self.helper.add_vary_by_cookie(request)
        return self.helper.identity(self.cookie, request)

    def authenticated_userid(self, request: Request) -> str | None:
        return Identity.authenticated_userid(self.identity(request))

    def permits(self, request: Request, context, permission: str) -> Allowed | Denied:
        return identity_permits(self.identity(request), context, permission)
