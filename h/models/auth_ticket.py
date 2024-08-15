from base64 import urlsafe_b64encode
from os import urandom

import sqlalchemy as sa

from h.db import Base
from h.db.mixins import Timestamps


class AuthTicket(Base, Timestamps):
    """
    An auth ticket.

    An auth ticket represents an open authentication session for a logged-in
    user. The ``id`` is typically stored in an ``auth`` cookie, provided by
    :py:class:`pyramid_authsanity.sources.CookieAuthSource`.
    """

    __tablename__ = "authticket"

    #: The id that is typically stored in the cookie, it should be a
    #: cryptographically random string with an appropriate amount of entropy.
    id = sa.Column(sa.UnicodeText(), primary_key=True)

    #: The datetime when this ticket expires
    expires = sa.Column(sa.DateTime, nullable=False)

    user_id = sa.Column(
        sa.Integer, sa.ForeignKey("user.id", ondelete="cascade"), nullable=False
    )

    #: The user whose auth ticket it is
    user = sa.orm.relationship("User")

    #: The user's userid, denormalised onto this table to avoid the need to do
    #: a SELECT against the user table just to find the authenticated_userid
    #: associated with the request.
    user_userid = sa.Column("user_userid", sa.UnicodeText(), nullable=False)

    @staticmethod
    def generate_ticket_id() -> str:
        """
        Return a new, unique, cryptographically secure id for use with an AuthTicket.

        Users don't have to use this method to generate AuthTicket ids: if you
        have your own requirements you can pass your own id into
        AuthTicket.__init__() instead. But this method is a good default way to
        generate ids for most cases.
        """
        return urlsafe_b64encode(urandom(32)).rstrip(b"=").decode("ascii")
