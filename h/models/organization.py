# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import sqlalchemy as sa

from h.db import Base
from h.db import mixins
from h import pubid

ORGANIZATION_DEFAULT_PUBID = "__default__"
ORGANIZATION_NAME_MIN_CHARS = 1
ORGANIZATION_NAME_MAX_CHARS = 25


class Organization(Base, mixins.Timestamps):
    __tablename__ = "organization"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # We don't expose the integer PK to the world, so we generate a short
    # random string to use as the publicly visible ID.
    pubid = sa.Column(sa.Text(), default=pubid.generate, unique=True, nullable=False)

    name = sa.Column(sa.UnicodeText(), nullable=False, index=True)

    logo = sa.Column(sa.UnicodeText())

    authority = sa.Column(sa.UnicodeText(), nullable=False)

    @sa.orm.validates("name")
    def validate_name(self, key, name):
        if not (
            ORGANIZATION_NAME_MIN_CHARS <= len(name) <= ORGANIZATION_NAME_MAX_CHARS
        ):
            raise ValueError(
                "name must be between {min} and {max} characters long".format(
                    min=ORGANIZATION_NAME_MIN_CHARS, max=ORGANIZATION_NAME_MAX_CHARS
                )
            )
        return name

    def __repr__(self):
        return "<Organization: %s>" % self.pubid

    @classmethod
    def default(cls, session):
        return session.query(cls).filter_by(pubid=ORGANIZATION_DEFAULT_PUBID).one()
