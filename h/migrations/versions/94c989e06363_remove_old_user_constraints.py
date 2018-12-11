"""
Remove old user constraints

These were created in b0e1a12de5e8 in order to avoid making that migration
irreversible. This is the irreversible part.

Revision ID: 94c989e06363
Revises: b0e1a12de5e8
Create Date: 2016-09-08 16:21:25.444258
"""

from __future__ import unicode_literals

from alembic import op


revision = "94c989e06363"
down_revision = "b0e1a12de5e8"


def upgrade():
    op.drop_constraint("uq__user__email_old", "user")
    op.drop_constraint("uq__user__uid_old", "user")
    op.drop_constraint("uq__user__username_old", "user")


def downgrade():
    pass
