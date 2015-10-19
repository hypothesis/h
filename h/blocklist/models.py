# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.orm import exc
from sqlalchemy.sql import expression

from h.db import Base
from h.i18n import TranslationString as _


class Blocklist(Base):

    """A list of URIs on which h will not launch."""

    __tablename__ = 'blocklist'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    uri = sa.Column(sa.UnicodeText(), nullable=False, unique=True)

    def __repr__(self):
        return self.uri

    @sa.orm.validates('uri')
    def validate_uri(self, key, uri):
        if self.get_by_uri(uri):
            raise ValueError(_("{uri} is already blocked.").format(uri=uri))
        else:
            return uri

    @classmethod
    def get_by_uri(cls, uri):
        try:
            return cls.query.filter(Blocklist.uri == uri).one()
        except exc.NoResultFound:
            return None

    @classmethod
    def all(cls):
        return cls.query.all()

    @classmethod
    def is_blocked(cls, uri):
        """Return True if the given URI is blocked."""
        if cls.query.filter(expression.literal(uri).like(cls.uri)).all():
            return True
        else:
            return False
