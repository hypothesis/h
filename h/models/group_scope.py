# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa

from h.db import Base


class GroupScope(Base):
    __tablename__ = 'groupscope'
    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    #: A fully qualified domain name, e.g. example.com, www.nytimes.com or
    #: web.hypothes.is.
    hostname = sa.Column(
        'hostname', sa.UnicodeText, nullable=False, unique=True)

    groups = sa.orm.relationship(
        'Group',
        secondary='group_groupscope',
        backref=sa.orm.backref('scopes'),
    )

    def __repr__(self):
        return '<GroupScope %s>' % self.hostname


GROUP_GROUPSCOPE_TABLE = sa.Table(
    'group_groupscope',
    Base.metadata,
    sa.Column(
        'group_id', sa.Integer, sa.ForeignKey('group.id'), nullable=False),
    sa.Column(
        'groupscope_id',
        sa.Integer,
        sa.ForeignKey('groupscope.id'),
        nullable=False),
    sa.PrimaryKeyConstraint('group_id', 'groupscope_id'),
)
