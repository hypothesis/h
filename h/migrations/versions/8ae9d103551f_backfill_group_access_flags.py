"""
Backfill group access flags.

Revision ID: 8ae9d103551f
Revises: af88524994ce
Create Date: 2016-11-29 12:51:31.247598
"""

import enum

import sqlalchemy as sa
from alembic import op

revision = "8ae9d103551f"
down_revision = "af88524994ce"


class JoinableBy(enum.Enum):
    authority = "authority"


joinable_type = sa.Enum(JoinableBy, name="group_joinable_by")


class ReadableBy(enum.Enum):
    members = "members"


readable_type = sa.Enum(ReadableBy, name="group_readable_by")


class WriteableBy(enum.Enum):
    members = "members"


writeable_type = sa.Enum(WriteableBy, name="group_writeable_by")

group_table = sa.table(
    "group",
    sa.Column("joinable_by", joinable_type, nullable=True),
    sa.Column("readable_by", readable_type, nullable=True),
    sa.Column("writeable_by", writeable_type, nullable=True),
)


def upgrade():
    op.execute(
        group_table.update().values(
            joinable_by=JoinableBy.authority,
            readable_by=ReadableBy.members,
            writeable_by=WriteableBy.members,
        )
    )


def downgrade():
    pass
