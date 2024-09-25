from datetime import datetime, timedelta

import sqlalchemy as sa

from h.models import AuthTicket


class AuthTicketService:
    TICKET_TTL = timedelta(days=90)

    # We only want to update the `expires` column when the tickets `expires` is
    # at least one minute smaller than the potential new value. This prevents
    # that we update the `expires` column on every single request.
    TICKET_REFRESH_INTERVAL = timedelta(minutes=1)

    def __init__(self, session, user_service):
        self._session = session
        self._user_service = user_service
        self._ticket = None

    def verify_ticket(
        self, userid: str | None, ticket_id: str | None
    ) -> AuthTicket | None:
        """
        Return the AuthTicket matching the given userid and ticket_id, or None.

        Verify that there is an unexpired AuthTicket in the DB matching the
        given `userid` and `ticket_id` and if so return the AuthTicket.
        """

        if self._ticket:
            # We've already verified this request's ticket.
            return self._ticket

        if not userid or not ticket_id:
            return None

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

        # Update the cache to allow quick checking if we are called again
        self._ticket = ticket

        return self._ticket

    def add_ticket(self, userid: str, ticket_id: str) -> None:
        """Add a new auth ticket for the given userid and token_id to the DB."""

        user = self._user_service.fetch(userid)

        if user is None:
            raise ValueError(f"Cannot find user with userid {userid}")

        ticket = AuthTicket(
            id=ticket_id,
            user=user,
            user_userid=user.userid,
            expires=datetime.utcnow() + self.TICKET_TTL,
        )

        self._session.add(ticket)

        # Update the cache to allow quick checking if we are called again.
        self._ticket = ticket

        return ticket

    def remove_ticket(self, ticket_id: str) -> None:
        """Remove any ticket with the given ID from the DB."""

        self._session.query(AuthTicket).filter_by(id=ticket_id).delete()

        # Empty the cache to force revalidation.
        self._ticket = None


def factory(_context, request):
    """Return a AuthTicketService instance for the passed context and request."""

    return AuthTicketService(request.db, user_service=request.find_service(name="user"))
