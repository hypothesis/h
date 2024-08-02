from datetime import datetime, timedelta

import sqlalchemy as sa
from webob.cookies import SignedCookieProfile

from h.models import AuthTicket, User


class AuthCookieService:
    TICKET_TTL = timedelta(days=7)

    # We only want to update the `expires` column when the tickets `expires` is
    # at least one minute smaller than the potential new value. This prevents
    # that we update the `expires` column on every single request.
    TICKET_REFRESH_INTERVAL = timedelta(minutes=1)

    def __init__(self, session, user_service, cookie):
        self._session = session
        self._user_service = user_service
        self._cookie = cookie
        self._user = None

    def verify_ticket(self, userid: str, ticket_id: str) -> User | None:
        """
        Return the User object matching the given userid and ticket_id, or None.

        Verify that there is an unexpired AuthTicket in the DB matching the
        given `userid` and `ticket_id` and if so return the User corresponding
        User object.
        """

        if self._user:
            # We've already vetted the user!
            return self._user

        ticket = (
            self._session.query(AuthTicket)
            .filter(
                AuthTicket.id == ticket_id,
                AuthTicket.user_userid == userid,
                # pylint:disable=not-callable
                AuthTicket.expires > sa.func.now(),
            )
            .one_or_none()
        )

        if ticket is None:
            return None

        # We don't want to update the `expires` column of an auth ticket on
        # every single request, but only when the ticket hasn't been touched
        # within a the defined `TICKET_REFRESH_INTERVAL`.
        if (datetime.utcnow() - ticket.updated) > self.TICKET_REFRESH_INTERVAL:
            ticket.expires = datetime.utcnow() + self.TICKET_TTL

        # Update the user cache to allow quick checking if we are called again
        self._user = ticket.user

        return self._user

    def add_ticket(self, userid: str, ticket_id: str) -> None:
        """Add a new auth ticket for the given userid and token_id to the DB."""

        # Update the user cache to allow quick checking if we are called again
        self._user = self._user_service.fetch(userid)
        if self._user is None:
            raise ValueError(f"Cannot find user with userid {userid}")

        ticket = AuthTicket(
            id=ticket_id,
            user=self._user,
            user_userid=self._user.userid,
            expires=datetime.utcnow() + self.TICKET_TTL,
        )
        self._session.add(ticket)

    def revoke_cookie(self):
        """
        Create headers to revoke the cookie used to log in a user.

        :return: An iterable of headers to return to the browser
        """

        _, ticket_id = self._get_cookie_value()
        if ticket_id:
            self._session.query(AuthTicket).filter_by(id=ticket_id).delete()

        # Empty the cached user to force revalidation
        self._user = None

        return self._cookie.get_headers(None, max_age=0)

    def _get_cookie_value(self):
        value = self._cookie.get_value()
        if not value:
            return None, None

        return value


def factory(_context, request):
    """Return a AuthCookieService instance for the passed context and request."""

    cookie = SignedCookieProfile(
        # This value is set in `h.auth` at the moment
        secret=request.registry.settings["h_auth_cookie_secret"],
        salt="authsanity",
        cookie_name="auth",
        max_age=30 * 24 * 3600,  # 30 days
        httponly=True,
        secure=request.scheme == "https",
    )

    return AuthCookieService(
        request.db,
        user_service=request.find_service(name="user"),
        cookie=cookie.bind(request),
    )
