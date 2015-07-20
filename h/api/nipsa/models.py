import sqlalchemy
from sqlalchemy.orm import exc

from h import db


class NipsaUser(db.Base):

    """A NIPSA entry for a user (SQLAlchemy ORM class)."""

    __tablename__ = 'nipsa'
    user_id = sqlalchemy.Column(sqlalchemy.UnicodeText, primary_key=True,
                                index=True)

    def __init__(self, user_id):
        self.user_id = user_id

    @classmethod
    def get_by_id(cls, user_id):
        """Return the NipsaUser object for the given user_id, or None."""
        try:
            return cls.query.filter(
                cls.user_id == user_id).one()
        except exc.NoResultFound:
            return None

    @classmethod
    def all(cls):
        """Return a list of all NipsaUser objects in the db."""
        return cls.query.all()
