from functools import lru_cache

from pyramid.request import Request
from webob.cookies import SignedCookieProfile

from h.models import AuthTicket
from h.security.identity import Identity
from h.services.auth_ticket import AuthTicketService


def is_api_request(request) -> bool:
    """Return True if `request` is an API request."""
    return bool(request.matched_route and request.matched_route.name.startswith("api."))


class AuthTicketCookieHelper:
    def identity(
        self, cookie: SignedCookieProfile, request: Request
    ) -> tuple[Identity, AuthTicket] | tuple[None, None]:
        userid, ticket_id = self.get_cookie_value(cookie)

        ticket = request.find_service(AuthTicketService).verify_ticket(
            userid, ticket_id
        )

        if (not ticket) or ticket.user.deleted:
            return (None, None)

        return (Identity.from_models(user=ticket.user), ticket)

    def add_ticket(self, request: Request, userid) -> AuthTicket:
        """
        Add a new auth ticket for the given user to the DB.

        Returns the the newly-created auth ticket.
        """
        return request.find_service(AuthTicketService).add_ticket(
            userid, AuthTicket.generate_ticket_id()
        )

    def remember(
        self, cookie: SignedCookieProfile, userid: str, auth_ticket: AuthTicket
    ):
        return cookie.get_headers([userid, auth_ticket.id])

    def forget(self, cookie: SignedCookieProfile, request: Request):
        request.session.invalidate()
        _, ticket_id = self.get_cookie_value(cookie)

        if ticket_id:
            request.find_service(AuthTicketService).remove_ticket(ticket_id)

        return cookie.get_headers(None, max_age=0)

    @staticmethod
    @lru_cache  # Ensure we only add this once per request
    def add_vary_by_cookie(request: Request):
        def vary_add(request, response):  # pylint:disable=unused-argument
            vary = set(response.vary if response.vary is not None else [])
            vary.add("Cookie")
            response.vary = list(vary)

        request.add_response_callback(vary_add)

    @staticmethod
    def get_cookie_value(cookie: SignedCookieProfile) -> tuple[str | None, str | None]:
        """
        Return the user ID and auth ticket ID from the given auth ticket cookie.

        Returns a `(user_id, auth_ticket_id)` 2-tuple or `(None, None)`.
        """
        return cookie.get_value() or (None, None)
