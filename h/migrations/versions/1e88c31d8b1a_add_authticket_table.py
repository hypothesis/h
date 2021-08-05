"""
Add authticket table.

Revision ID: 1e88c31d8b1a
Revises: f9d3058bec5f
Create Date: 2016-09-16 12:22:26.480404
"""

import sqlalchemy as sa
from alembic import op

revision = "1e88c31d8b1a"
down_revision = "f9d3058bec5f"


def upgrade():
    op.create_table(
        "authticket",
        sa.Column("id", sa.UnicodeText(), primary_key=True),
        sa.Column("created", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("expires", sa.DateTime, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("user_userid", sa.UnicodeText(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="cascade"),
    )


def downgrade():
    op.drop_table("authticket")
