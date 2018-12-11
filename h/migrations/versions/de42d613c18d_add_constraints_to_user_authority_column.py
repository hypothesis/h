"""
Add constraints to user authority column

Revision ID: de42d613c18d
Revises: 2e2cc6a0c521
Create Date: 2016-08-15 18:18:19.037667
"""

from __future__ import unicode_literals

from alembic import op


revision = "de42d613c18d"
down_revision = "2e2cc6a0c521"


def upgrade():
    op.alter_column("user", "authority", nullable=False)


def downgrade():
    op.alter_column("user", "authority", nullable=True)
