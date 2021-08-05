import sqlalchemy as sa
from sqlalchemy.sql import expression

from h.db import Base


class Blocklist(Base):
    """
    A list of URIs for which the badge API will always return 0.

    This means that the Chrome extension will never show a number of
    annotations on its badge for these URIs.

    """

    __tablename__ = "blocklist"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    uri = sa.Column(sa.UnicodeText(), nullable=False, unique=True)

    def __repr__(self):
        return self.uri

    @classmethod
    def is_blocked(cls, session, uri):
        """Return True if the given URI is blocked."""
        uri_matches = expression.literal(uri).like(cls.uri)
        return session.query(cls).filter(uri_matches).count() > 0
