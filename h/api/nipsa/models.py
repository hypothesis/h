# -*- coding: utf-8 -*-
import sqlalchemy
from sqlalchemy.orm import exc

from h.api import db


class NipsaUser(db.Base):

    """A NIPSA entry for a user (SQLAlchemy ORM class)."""

    __tablename__ = 'nipsa'
    userid = sqlalchemy.Column(
        sqlalchemy.UnicodeText(), primary_key=True)

    def __init__(self, userid):
        self.userid = userid

    @classmethod
    def get_by_userid(cls, userid):
        """Return the NipsaUser object for the given userid, or None."""
        try:
            return cls.query.filter(
                cls.userid == userid).one()
        except exc.NoResultFound:
            return None

    @classmethod
    def all(cls):
        """Return a list of all NipsaUser objects in the db."""
        return cls.query.all()
