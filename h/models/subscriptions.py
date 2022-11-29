from enum import Enum

import sqlalchemy as sa

from h.db import Base


class Subscriptions(Base):
    """Permission from the user to send different types of communication."""

    class Type(str, Enum):
        """All the different types of subscriptions we support.

        This isn't integrated with the type field, but it would be nice if it
        was.
        """

        REPLY = "reply"

    __tablename__ = "subscriptions"
    __table_args__ = (sa.Index("subs_uri_idx_subscriptions", "uri"),)

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    uri = sa.Column(sa.UnicodeText(), nullable=False)
    type = sa.Column(sa.VARCHAR(64), nullable=False)
    active = sa.Column(sa.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Subscription uri={self.uri} type={self.type} active={self.active}>"
