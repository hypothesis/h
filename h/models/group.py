# -*- coding: utf-8 -*-

from collections import namedtuple

import enum
import sqlalchemy as sa
from pyramid import security
from sqlalchemy.orm import exc
import slugify

from h.db import Base
from h.db import mixins
from h import pubid


GROUP_NAME_MIN_LENGTH = 4
GROUP_NAME_MAX_LENGTH = 25
GROUP_DESCRIPTION_MAX_LENGTH = 250


class GroupFactory(object):
    def __init__(self, request):
        self.request = request

    def __getitem__(self, pubid):
        try:
            return self.request.db.query(Group).filter_by(pubid=pubid).one()
        except exc.NoResultFound:
            raise KeyError()


class JoinableBy(enum.Enum):
    authority = 'authority'


class ReadableBy(enum.Enum):
    members = 'members'
    world = 'world'


class WriteableBy(enum.Enum):
    authority = 'authority'
    members = 'members'


class Group(Base, mixins.Timestamps):
    __tablename__ = 'group'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    # We don't expose the integer PK to the world, so we generate a short
    # random string to use as the publicly visible ID.
    pubid = sa.Column(sa.Text(),
                      default=pubid.generate,
                      unique=True,
                      nullable=False)
    authority = sa.Column(sa.UnicodeText(), nullable=False)
    name = sa.Column(sa.UnicodeText(), nullable=False, index=True)

    creator_id = sa.Column(
        sa.Integer, sa.ForeignKey('user.id'))
    creator = sa.orm.relationship('User')

    description = sa.Column(sa.UnicodeText())

    #: Which type of user is allowed to join this group, possible values are:
    #: authority, None
    joinable_by = sa.Column(sa.Enum(JoinableBy, name='group_joinable_by'),
                            nullable=True)

    #: Which type of user is allowed to read annotations in this group,
    #: possible values are: authority, members, world
    readable_by = sa.Column(sa.Enum(ReadableBy, name='group_readable_by'),
                            nullable=True, index=True)

    #: Which type of user is allowed to write to this group, possible values
    #: are: authority, members
    writeable_by = sa.Column(sa.Enum(WriteableBy, name='group_writeable_by'),
                             nullable=True)

    # Group membership
    members = sa.orm.relationship(
        'User', secondary='user_group', backref=sa.orm.backref(
            'groups', order_by='Group.name'))

    scopes = sa.orm.relationship('GroupScope', backref='group', cascade='all, delete-orphan')

    organization_id = sa.Column(sa.Integer, sa.ForeignKey('organization.id'), nullable=False)
    organization = sa.orm.relationship('Organization')

    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)

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

    @property
    def type(self):
        """
        The "type" of this group, e.g. "open" or "private".

        :rtype: string
        :raises ValueError: if the type of the group isn't recognized

        """
        self_type_flags = TypeFlags(
            joinable_by=self.joinable_by,
            readable_by=self.readable_by,
            writeable_by=self.writeable_by)

        for type_, type_flags in (('open', OPEN_GROUP_TYPE_FLAGS), ('private', PRIVATE_GROUP_TYPE_FLAGS), ('restricted', RESTRICTED_GROUP_TYPE_FLAGS)):
            if self_type_flags == type_flags:
                return type_

        raise ValueError(
            "This group doesn't seem to match any known type of group. "
            "This shouldn't be in the database!")

    @property
    def is_public(self):
        return self.readable_by == ReadableBy.world

    def __acl__(self):
        terms = []

        join_principal = _join_principal(self)
        if join_principal is not None:
            terms.append((security.Allow, join_principal, 'join'))

        read_principal = _read_principal(self)
        if read_principal is not None:
            terms.append((security.Allow, read_principal, 'read'))

        write_principal = _write_principal(self)
        if write_principal is not None:
            terms.append((security.Allow, write_principal, 'write'))

        if self.creator:
            terms.append((security.Allow, self.creator.userid, 'admin'))
        terms.append(security.DENY_ALL)

        return terms

    def __repr__(self):
        return '<Group: %s>' % self.slug

    @classmethod
    def created_by(cls, session, user):
        """Return a query object filtering groups by creator."""
        return session.query(cls).filter(Group.creator == user)


def _join_principal(group):
    return {
        JoinableBy.authority: 'authority:{}'.format(group.authority),
    }.get(group.joinable_by)


def _read_principal(group):
    return {
        ReadableBy.members: 'group:{}'.format(group.pubid),
        ReadableBy.world: security.Everyone,
    }.get(group.readable_by)


def _write_principal(group):
    return {
        WriteableBy.authority: 'authority:{}'.format(group.authority),
        WriteableBy.members: 'group:{}'.format(group.pubid),
    }.get(group.writeable_by)


TypeFlags = namedtuple('TypeFlags', 'joinable_by readable_by writeable_by')


OPEN_GROUP_TYPE_FLAGS = TypeFlags(
    joinable_by=None,
    readable_by=ReadableBy.world,
    writeable_by=WriteableBy.authority)


PRIVATE_GROUP_TYPE_FLAGS = TypeFlags(
    joinable_by=JoinableBy.authority,
    readable_by=ReadableBy.members,
    writeable_by=WriteableBy.members)


RESTRICTED_GROUP_TYPE_FLAGS = TypeFlags(
    joinable_by=None,
    readable_by=ReadableBy.world,
    writeable_by=WriteableBy.members)


USER_GROUP_TABLE = sa.Table(
    'user_group', Base.metadata,
    sa.Column('id', sa.Integer, autoincrement=True, primary_key=True),
    sa.Column('user_id',
              sa.Integer,
              sa.ForeignKey('user.id'),
              nullable=False),
    sa.Column('group_id',
              sa.Integer,
              sa.ForeignKey('group.id'),
              nullable=False),
    sa.UniqueConstraint('user_id', 'group_id'),
)
