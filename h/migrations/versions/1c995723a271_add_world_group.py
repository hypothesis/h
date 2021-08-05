"""
Add world group.

Revision ID: 1c995723a271
Revises: 21b1ce37e327
Create Date: 2017-04-18 12:19:33.863557
"""

import enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "1c995723a271"
down_revision = "21b1ce37e327"

Base = declarative_base()
Session = sessionmaker()


class ReadableBy(enum.Enum):
    world = "world"


class WriteableBy(enum.Enum):
    authority = "authority"


class Group(Base):
    __tablename__ = "group"
    id = sa.Column(sa.Integer, primary_key=True)
    pubid = sa.Column(sa.Text())
    authority = sa.Column(sa.UnicodeText())
    name = sa.Column(sa.UnicodeText())
    readable_by = sa.Column(sa.Enum(ReadableBy, name="group_readable_by"))
    writeable_by = sa.Column(sa.Enum(WriteableBy, name="group_writeable_by"))


def upgrade():
    session = Session(bind=op.get_bind())
    world_group = Group(
        name="Public",
        pubid="__world__",
        authority="hypothes.is",
        readable_by=ReadableBy.world,
        writeable_by=WriteableBy.authority,
    )
    session.add(world_group)
    session.commit()


def downgrade():
    session = Session(bind=op.get_bind())
    session.query(Group).filter_by(pubid="__world__").delete()
    session.commit()
