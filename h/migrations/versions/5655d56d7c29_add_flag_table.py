"""
Add flag table.

Revision ID: 5655d56d7c29
Revises: c322c57b49db
Create Date: 2017-03-08 15:32:27.288684
"""

import sqlalchemy as sa
from alembic import op

from h.db import types

revision = "5655d56d7c29"
down_revision = "c322c57b49db"


def upgrade():
    op.create_table(
        "flag",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("annotation_id", types.URLSafeUUID, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["annotation_id"], ["annotation.id"], ondelete="cascade"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="cascade"),
        sa.UniqueConstraint("annotation_id", "user_id"),
    )


def downgrade():
    op.drop_table("flag")
