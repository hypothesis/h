# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa

from h._compat import urlparse
from h.db import Base, mixins


class GroupScope(Base):
    __tablename__ = 'groupscope'
    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    #: A fully qualified domain name, e.g. example.com, www.nytimes.com or
    #: web.hypothes.is.
    hostname = sa.Column('hostname', sa.UnicodeText)

    groups = sa.orm.relationship(
        'Group',
        secondary='groupscope_group',
        backref=sa.orm.backref('scopes', order_by='Group.name'),
    )

    def __repr__(self):
        return '<GroupScope %s>' % self.id


GROUP_GROUPSCOPE_TABLE = sa.Table('groupscope_group', Base.metadata,
    sa.Column('id', sa.Integer, autoincrement=True, primary_key=True),
    sa.Column('group_id', sa.Integer, sa.ForeignKey('group.id')),
    sa.Column('groupscope_id', sa.Integer, sa.ForeignKey('groupscope.id')),
    sa.UniqueConstraint('group_id', 'groupscope_id'),
)
