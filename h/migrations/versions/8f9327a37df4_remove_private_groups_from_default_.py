# -*- coding: utf-8 -*-
"""
Remove private groups from (default) organization.

In the past, we had associated private groups (those groups with
:py:attr:`ReadableBy.members`, :py:attr:`JoinableBy.authority`)
with the default organization (organization with
:py:attr:`h.models.Organization.pubid` = ``__default__``) because the
group -> organization relationship was non-nullable.

Now that a group may have a null organization, set all private group
organizations to ``NULL``, as they were put "into" the default organization
simply to satisfy the DB constraint of having an organization.

At time of migration writing, it is the intent that, for now, private groups
do not belong to organizations.
"""

from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import logging
import enum
import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


revision = "8f9327a37df4"
down_revision = "5d256923d642"


log = logging.getLogger(__name__)

Base = declarative_base()
Session = sessionmaker()


class JoinableBy(enum.Enum):
    authority = 'authority'


class ReadableBy(enum.Enum):
    members = 'members'
    world = 'world'


class Organization(Base):
    __tablename__ = 'organization'
    id = sa.Column(sa.Integer, primary_key=True)


class Group(Base):
    __tablename__ = 'group'
    id = sa.Column(sa.Integer, primary_key=True)
    organization_id = sa.Column(sa.Integer, sa.ForeignKey('organization.id'), nullable=True)
    readable_by = sa.Column(sa.Enum(ReadableBy, name='group_readable_by'))
    joinable_by = sa.Column(sa.Enum(JoinableBy, name='group_joinable_by'))


def upgrade():
    session = Session(bind=op.get_bind())
    private_groups = session.query(Group).filter_by(readable_by=ReadableBy.members,
                                                    joinable_by=JoinableBy.authority).all()
    removed_count = 0

    for group in private_groups:
        if group.organization_id is not None:
            group.organization_id = None
            removed_count += 1

    session.commit()

    log.info("Removed {n} private groups from organizations".format(n=removed_count))


def downgrade():
    pass
