# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from pyramid_authsanity import interfaces
import sqlalchemy as sa
from zope import interface
from zope.sqlalchemy import mark_changed

from h.models import AuthTicket
from h.auth.util import principals_for_user

TICKET_TTL = datetime.timedelta(days=7)


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
            raise AuthTicketNotLoadedError('auth ticket is not loaded yet')

        return self._userid

    def groups(self):
        """Returns security principals of the logged-in user."""

        if self._userid is None:
            raise AuthTicketNotLoadedError('auth ticket is not loaded yet')

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

        # Since we load and then update the AuthTicket.expires on every request,
        # we optimise it with a `UPDATE ... RETURNING` query, doing both of
        # these in one. When the returned `userid` is `None` then the
        # authentication failed, otherwise it succeeded. Doing a query like this
        # will not mark the session as dirty, and thus the transaction will
        # get rolled back at the end, unless we found a userid, at which point
        # we manually mark the session as changed.
        ticket_query = (sa.update(AuthTicket.__table__)
                        .where(sa.and_(AuthTicket.id == ticket_id,
                                       AuthTicket.user_userid == principal,
                                       AuthTicket.expires > sa.func.now()))
                        .values(expires=(sa.func.now() + TICKET_TTL))
                        .returning(AuthTicket.user_userid))
        self._userid = self.session.execute(ticket_query).scalar()

        if self._userid:
            mark_changed(self.session)
            return True

        return False

    def add_ticket(self, principal, ticket_id):
        """Store a new ticket with the given id and principal in the database."""

        user = self.usersvc.fetch(principal)
        if user is None:
            raise ValueError('Cannot find user with userid %s' % principal)

        ticket = AuthTicket(id=ticket_id,
                            user=user,
                            user_userid=user.userid,
                            expires=(datetime.datetime.utcnow() + TICKET_TTL))
        self.session.add(ticket)
        # We cache the new userid, this will allow us to migrate the old
        # session policy to this new ticket policy.
        self._userid = user.userid

    def remove_ticket(self, ticket_id):
        """Delete a ticket by id from the database."""

        if ticket_id:
            self.session.query(AuthTicket).filter_by(id=ticket_id).delete()
        self._userid = None


def auth_ticket_service_factory(context, request):
    """Return a AuthTicketService instance for the passed context and request."""
    user_service = request.find_service(name='user')
    return AuthTicketService(request.db, user_service)
