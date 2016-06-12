# -*- coding: utf-8 -*-

import sqlalchemy as sa

from h import db


class NipsaUser(db.Base):

    """A NIPSA entry for a user (SQLAlchemy ORM class)."""

    __tablename__ = 'nipsa'
    userid = sa.Column(sa.UnicodeText(), primary_key=True)

    def __init__(self, userid):
        self.userid = userid
