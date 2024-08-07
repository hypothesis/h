import base64
from functools import lru_cache
from os import urandom

import webob
from pyramid.security import Allowed, Denied

from h.security.identity import Identity
from h.security.permits import identity_permits
from h.services.auth_ticket import AuthTicketService


class CookiePolicy:
    """
    An authentication policy based on cookies.

    This policy kicks in when accessing the UI presented by `h` and also boot
    straps the login for the client (when the popup shows).
    """

    def __init__(self, cookie: webob.cookies.SignedCookieProfile):
        self.cookie = cookie

    def identity(self, request):
        self._add_vary_by_cookie(request)

        userid, ticket_id = self._get_cookie_value()

        user = request.find_service(AuthTicketService).verify_ticket(userid, ticket_id)

        if (not user) or user.deleted:
            return None

        return Identity.from_models(user=user)

    def authenticated_userid(self, request):
        return Identity.authenticated_userid(self.identity(request))

    def remember(self, request, userid, **kw):  # pylint:disable=unused-argument
        """Get a list of headers which will remember the user in a cookie."""

        self._add_vary_by_cookie(request)

        previous_userid = self.authenticated_userid(request)

        # Clear the previous session
        if previous_userid != userid:
            request.session.invalidate()
        else:
            # We are logging in the same user that is already logged in, we
            # still want to generate a new session, but we can keep the
            # existing data
            data = dict(request.session.items())
            request.session.invalidate()
            request.session.update(data)
            request.session.new_csrf_token()

        ticket_id = base64.urlsafe_b64encode(urandom(32)).rstrip(b"=").decode("ascii")
        request.find_service(AuthTicketService).add_ticket(userid, ticket_id)
        return self.cookie.get_headers([userid, ticket_id])

    def forget(self, request):
        """Get a list of headers which will delete appropriate cookies."""

        self._add_vary_by_cookie(request)

        # Clear the session by invalidating it
        request.session.invalidate()

        _, ticket_id = self._get_cookie_value()

        if ticket_id:
            request.find_service(AuthTicketService).remove_ticket(ticket_id)

        return self.cookie.get_headers(None, max_age=0)

    def permits(self, request, context, permission) -> Allowed | Denied:
        return identity_permits(self.identity(request), context, permission)

    @staticmethod
    @lru_cache  # Ensure we only add this once per request
    def _add_vary_by_cookie(request):
        def vary_add(request, response):  # pylint:disable=unused-argument
            vary = set(response.vary if response.vary is not None else [])
            vary.add("Cookie")
            response.vary = list(vary)

        request.add_response_callback(vary_add)

    def _get_cookie_value(self):
        return self.cookie.get_value() or (None, None)
