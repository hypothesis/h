"""
Add a unique constraint to user_group table.

Revision ID: e17d3ce4fcd2
Revises: 9e01b7287da2
Create Date: 2016-07-08 18:56:20.118573
"""

from alembic import op

revision = "e17d3ce4fcd2"
down_revision = "9e01b7287da2"


def upgrade():
    op.create_unique_constraint(
        "uq__user_group__user_id", "user_group", ["user_id", "group_id"]
    )


def downgrade():
    op.drop_constraint("uq__user_group__user_id", "user_group")
