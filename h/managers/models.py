# coding=utf8

import sqlalchemy as sa
from sqlalchemy.orm import exc

from h.db import Base
from h.db import mixins


class Manager(Base, mixins.Timestamps):
    __tablename__ = 'manager'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    user = sa.orm.relationship('User', foreign_keys=[user_id])

    url = sa.Column("url", sa.UnicodeText(), nullable=False)

    def __init__(self, user, url):
        self.user = user
        self.url = url

    def __repr__(self):
        return '<Manager: %s>' % self.id

    @classmethod
    def get_by_id_user(cls, manager_id, user):
        """Query by id."""
        return cls.query.filter(cls.id == manager_id, user=user).first()

    @classmethod
    def get_by_user(cls, user):
        """Return All Followers of user."""
        return cls.query.filter(cls.user == user)
