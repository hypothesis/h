"""
Add group access flags.

Revision ID: af88524994ce
Revises: 8990247b876c
Create Date: 2016-11-25 15:58:59.517470
"""

import enum

import sqlalchemy as sa
from alembic import op

revision = "af88524994ce"
down_revision = "8990247b876c"


class JoinableBy(enum.Enum):
    authority = "authority"


joinable_type = sa.Enum(JoinableBy, name="group_joinable_by")


class ReadableBy(enum.Enum):
    authority = "authority"
    members = "members"
    world = "world"


readable_type = sa.Enum(ReadableBy, name="group_readable_by")


class WriteableBy(enum.Enum):
    authority = "authority"
    members = "members"


writeable_type = sa.Enum(WriteableBy, name="group_writeable_by")


def upgrade():
    joinable_type.create(op.get_bind())
    op.add_column("group", sa.Column("joinable_by", joinable_type, nullable=True))

    readable_type.create(op.get_bind())
    op.add_column("group", sa.Column("readable_by", readable_type, nullable=True))

    writeable_type.create(op.get_bind())
    op.add_column("group", sa.Column("writeable_by", writeable_type, nullable=True))


def downgrade():
    op.drop_column("group", "joinable_by")
    joinable_type.drop(op.get_bind())

    op.drop_column("group", "readable_by")
    readable_type.drop(op.get_bind())

    op.drop_column("group", "writeable_by")
    writeable_type.drop(op.get_bind())
