import datetime

import sqlalchemy as sa

from h import models

TICKET_TTL = datetime.timedelta(days=7)

# We only want to update the `expires` column when the tickets `expires` is at
# least one minute smaller than the potential new value. This prevents that we
# update the `expires` column on every single request.
TICKET_REFRESH_INTERVAL = datetime.timedelta(minutes=1)


class AuthTicketService:
    def __init__(self, session, user_service):
        self.session = session
        self.user_service = user_service

        self.user = None

    def verify_ticket(self, userid, ticket_id):
        """
        Verify an authentication claim (from a cookie) against the stored tickets.

        This will only successfully verify a ticket when it is found in the
        database, the principal is the same, and it hasn't expired yet.
        """
        ticket = (
            self.session.query(models.AuthTicket)
            .filter(
                models.AuthTicket.id == ticket_id,
                models.AuthTicket.user_userid == userid,
                models.AuthTicket.expires > sa.func.now(),
            )
            .one_or_none()
        )

        if ticket is None:
            return None

        self.user = ticket.user

        # We don't want to update the `expires` column of an auth ticket on
        # every single request, but only when the ticket hasn't been touched
        # within a the defined `TICKET_REFRESH_INTERVAL`.
        if (utcnow() - ticket.updated) > TICKET_REFRESH_INTERVAL:
            ticket.expires = utcnow() + TICKET_TTL

        return self.user

    def add_ticket(self, userid, ticket_id):
        """Store a new ticket with the user and ticket id in the database."""

        self.user = self.user_service.fetch(userid)
        if self.user is None:
            raise ValueError("Cannot find user with userid %s" % userid)

        ticket = models.AuthTicket(
            id=ticket_id,
            user=self.user,
            user_userid=self.user.userid,
            expires=(utcnow() + TICKET_TTL),
        )
        self.session.add(ticket)

    def remove_ticket(self, ticket_id):
        """Delete a ticket by id from the database."""

        if ticket_id:
            self.session.query(models.AuthTicket).filter_by(id=ticket_id).delete()
        self.user = None


def auth_ticket_service_factory(_context, request):
    """Return a AuthTicketService instance for the passed context and request."""
    user_service = request.find_service(name="user")
    return AuthTicketService(request.db, user_service)


def utcnow():
    return datetime.datetime.utcnow()
