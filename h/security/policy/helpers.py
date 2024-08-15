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
    ) -> Identity | None:
        userid, ticket_id = self.get_cookie_value(cookie)

        user = request.find_service(AuthTicketService).verify_ticket(userid, ticket_id)

        if (not user) or user.deleted:
            return None

        return Identity.from_models(user=user)

    def remember(self, cookie: SignedCookieProfile, request: Request, userid: str):
        ticket_id = AuthTicket.generate_ticket_id()
        request.find_service(AuthTicketService).add_ticket(userid, ticket_id)
        return cookie.get_headers([userid, ticket_id])

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
    def get_cookie_value(cookie: SignedCookieProfile):
        return cookie.get_value() or (None, None)
