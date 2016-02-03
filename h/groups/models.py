# -*- coding: utf-8 -*-
import datetime

import sqlalchemy as sa
from sqlalchemy.orm import exc
import slugify

from h.db import Base
from h import pubid


GROUP_NAME_MIN_LENGTH = 4
GROUP_NAME_MAX_LENGTH = 25


class Group(Base):
    __tablename__ = 'group'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    # We don't expose the integer PK to the world, so we generate a short
    # random string to use as the publicly visible ID.
    pubid = sa.Column(sa.Text(),
                      default=pubid.generate,
                      unique=True,
                      nullable=False)
    name = sa.Column(sa.UnicodeText(), nullable=False)
    created = sa.Column(sa.DateTime,
                        default=datetime.datetime.utcnow,
                        server_default=sa.func.now(),
                        nullable=False)
    updated = sa.Column(sa.DateTime,
                        server_default=sa.func.now(),
                        default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow,
                        nullable=False)

    # We store information about who created the group -- we don't use this
    # currently, but it seems careless to lose this information when in the
    # future these people may be the first admins of their groups.
    creator_id = sa.Column(
        sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    creator = sa.orm.relationship('User')

    # Group membership
    members = sa.orm.relationship('User',
                                  secondary='user_group',
                                  backref='groups')

    def __init__(self, name, creator):
        self.name = name
        self.creator = creator
        self.members.append(creator)

    @sa.orm.validates('name')
    def validate_name(self, key, name):
        if not GROUP_NAME_MIN_LENGTH <= len(name) <= GROUP_NAME_MAX_LENGTH:
            raise ValueError('name must be between {min} and {max} characters '
                             'long'.format(min=GROUP_NAME_MIN_LENGTH,
                                           max=GROUP_NAME_MAX_LENGTH))
        return name

    @property
    def slug(self):
        """A version of this group's name suitable for use in a URL."""
        return slugify.slugify(self.name)

    def __repr__(self):
        return '<Group: %s>' % self.slug

    @classmethod
    def get_by_pubid(cls, pubid):
        """Return the group with the given pubid, or None."""
        return cls.query.filter(cls.pubid == pubid).first()

    @classmethod
    def get_by_id(cls, id_):
        """Return the group with the given id, or None."""
        try:
            return cls.query.filter(
                cls.id == id_).one()
        except exc.NoResultFound:
            return None

    @classmethod
    def created_by(cls, user):
        """Return a query object filtering groups by creator."""
        return cls.query.filter(Group.creator == user)


USER_GROUP_TABLE = sa.Table(
    'user_group', Base.metadata,
    sa.Column('user_id',
              sa.Integer,
              sa.ForeignKey('user.id'),
              nullable=False),
    sa.Column('group_id',
              sa.Integer,
              sa.ForeignKey('group.id'),
              nullable=False)
)
