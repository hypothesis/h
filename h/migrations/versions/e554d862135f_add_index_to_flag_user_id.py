"""
Add index to flag.user_id

Revision ID: e554d862135f
Revises: 5655d56d7c29
Create Date: 2017-03-16 12:35:45.791202
"""

from __future__ import unicode_literals

from alembic import op


revision = "e554d862135f"
down_revision = "5655d56d7c29"


def upgrade():
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__flag__user_id"),
        "flag",
        ["user_id"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__flag__user_id"), "flag")
