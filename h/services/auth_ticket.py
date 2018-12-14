# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from pyramid_authsanity import interfaces
import sqlalchemy as sa
from zope import interface

from h import models
from h.auth.util import principals_for_user

TICKET_TTL = datetime.timedelta(days=7)

# We only want to update the `expires` column when the tickets `expires` is at
# least one minute smaller than the potential new value. This prevents that we
# update the `expires` column on every single request.
TICKET_REFRESH_INTERVAL = datetime.timedelta(minutes=1)


class AuthTicketNotLoadedError(Exception):
    pass


@interface.implementer(interfaces.IAuthService)
class AuthTicketService(object):
    def __init__(self, session, user_service):
        self.session = session
        self.usersvc = user_service

        self._userid = None

    def userid(self):
        """
        Return current userid, or None.

        Raises ``AuthTicketNotLoadedError`` when auth ticket has not been
        loaded yet, which signals the auth policy to call ``verify_ticket``.
        """

        if self._userid is None:
            raise AuthTicketNotLoadedError("auth ticket is not loaded yet")

        return self._userid

    def groups(self):
        """Returns security principals of the logged-in user."""

        if self._userid is None:
            raise AuthTicketNotLoadedError("auth ticket is not loaded yet")

        user = self.usersvc.fetch(self._userid)
        return principals_for_user(user)

    def verify_ticket(self, principal, ticket_id):
        """
        Verifies an authentication claim (usually extracted from a cookie)
        against the stored tickets.

        This will only successfully verify a ticket when it is found in the
        database, the principal is the same, and it hasn't expired yet.
        """

        if ticket_id is None:
            return False

        ticket = (
            self.session.query(models.AuthTicket)
            .filter(
                models.AuthTicket.id == ticket_id,
                models.AuthTicket.user_userid == principal,
                models.AuthTicket.expires > sa.func.now(),
            )
            .one_or_none()
        )

        if ticket is None:
            return False

        self._userid = ticket.user_userid

        # We don't want to update the `expires` column of an auth ticket on
        # every single request, but only when the ticket hasn't been touched
        # within a the defined `TICKET_REFRESH_INTERVAL`.
        if (utcnow() - ticket.updated) > TICKET_REFRESH_INTERVAL:
            ticket.expires = utcnow() + TICKET_TTL

        return True

    def add_ticket(self, principal, ticket_id):
        """Store a new ticket with the given id and principal in the database."""

        user = self.usersvc.fetch(principal)
        if user is None:
            raise ValueError("Cannot find user with userid %s" % principal)

        ticket = models.AuthTicket(
            id=ticket_id,
            user=user,
            user_userid=user.userid,
            expires=(utcnow() + TICKET_TTL),
        )
        self.session.add(ticket)
        # We cache the new userid, this will allow us to migrate the old
        # session policy to this new ticket policy.
        self._userid = user.userid

    def remove_ticket(self, ticket_id):
        """Delete a ticket by id from the database."""

        if ticket_id:
            self.session.query(models.AuthTicket).filter_by(id=ticket_id).delete()
        self._userid = None


def auth_ticket_service_factory(context, request):
    """Return a AuthTicketService instance for the passed context and request."""
    user_service = request.find_service(name="user")
    return AuthTicketService(request.db, user_service)


def utcnow():
    return datetime.datetime.utcnow()
