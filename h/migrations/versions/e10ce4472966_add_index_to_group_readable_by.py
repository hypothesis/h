"""
Add index to group.readable_by

Revision ID: e10ce4472966
Revises: f0f42ffaa27d
Create Date: 2016-12-22 16:13:53.658938
"""

from __future__ import unicode_literals

from alembic import op


revision = "e10ce4472966"
down_revision = "f0f42ffaa27d"


def upgrade():
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__group__readable_by"),
        "group",
        ["readable_by"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade():
    op.drop_index(op.f("ix__group__readable_by"), "group")
