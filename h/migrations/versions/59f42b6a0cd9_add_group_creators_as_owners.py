"""Add existing group creators as owners."""

from alembic import op
from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, select, update
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()


user_table = Table("user", metadata, Column("id", Integer, primary_key=True))


group_table = Table(
    "group",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("creator_id", Integer, ForeignKey("user.id")),
)


user_group_table = Table(
    "user_group",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("group_id", Integer, ForeignKey("group.id")),
    Column("roles", JSONB),
)


revision = "59f42b6a0cd9"
down_revision = "1975edef158d"


def upgrade():
    op.execute(
        update(user_group_table)
        .where(
            user_group_table.c.id.in_(
                select(user_group_table.c.id)
                .where(user_group_table.c.group_id == group_table.c.id)
                .where(user_group_table.c.user_id == user_table.c.id)
                .where(user_table.c.id == group_table.c.creator_id)
            )
        )
        .values(roles=["owner"])
    )


def downgrade():
    pass
