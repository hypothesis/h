from pyramid.request import Request
from pyramid.security import Allowed, Denied

from h.security.identity import Identity
from h.security.policy._cookie import CookiePolicy

COOKIE_AUTHENTICATABLE_API_REQUESTS = [
    ("api.groups", "POST"),  # Create a new group.
    ("api.group", "PATCH"),  # Edit an existing group.
]


class APICookiePolicy:
    """Authenticate API requests with cookies."""

    def __init__(self, cookie_policy: CookiePolicy):
        self.cookie_policy = cookie_policy

    @staticmethod
    def handles(request: Request) -> bool:
        """Return True if this policy applies to `request`."""
        return (
            request.matched_route.name,
            request.method,
        ) in COOKIE_AUTHENTICATABLE_API_REQUESTS

    def identity(self, request: Request) -> Identity | None:
        return self.cookie_policy.identity(request)

    def authenticated_userid(self, request: Request) -> str | None:
        return self.cookie_policy.authenticated_userid(request)

    def permits(self, request: Request, context, permission: str) -> Allowed | Denied:
        return self.cookie_policy.permits(request, context, permission)
