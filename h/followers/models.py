# coding=utf8
import sqlalchemy as sa
from sqlalchemy.orm import exc

from h.db import Base
from h.db import mixins

class Follower(Base, mixins.Timestamps):
    __tablename__ = 'follow'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    me_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    me = sa.orm.relationship('User', foreign_keys=[me_id])

    follow_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    follow = sa.orm.relationship('User', foreign_keys=[follow_id])

    def __init__(self, me, follow):
        self.me =me
        self.follow = follow

    def __repr__(self):
        return '<Follow: %s>' % self.id

    @classmethod
    def get_by_user_and_follower(cls, session, follow, me):
        """Query by user and follower."""
        return session.query(cls).filter(cls.follow == follow, cls.me == me).first()

    @classmethod
    def get_followers(cls, session, user):
        """Return ALL Followers of user."""
        return session.query(cls).filter(cls.follow == user).all()

    @classmethod
    def get_following(cls,session, user):
        """Return ALL Following of user."""
        return session.query(cls).filter(cls.me == user).all()
    @classmethod
    def get_all(cls, session):
        """Return ALL Following of user."""
        return session.query(cls).all()
