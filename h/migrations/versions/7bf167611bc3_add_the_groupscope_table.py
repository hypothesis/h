"""
Add the groupscope table.

Revision ID: 7bf167611bc3
Revises: c943c3f8a7e5
Create Date: 2018-02-08 11:00:50.420618
"""

import sqlalchemy as sa
from alembic import op

revision = "7bf167611bc3"
down_revision = "c943c3f8a7e5"


def upgrade():
    op.create_table(
        "groupscope",
        sa.Column("id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column(
            "group_id",
            sa.Integer,
            sa.ForeignKey("group.id", ondelete="cascade"),
            nullable=False,
        ),
        sa.Column("origin", sa.UnicodeText, nullable=False),
    )


def downgrade():
    op.drop_table("groupscope")
