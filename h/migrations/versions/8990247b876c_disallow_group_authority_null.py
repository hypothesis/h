"""
Disallow group.authority null

Revision ID: 8990247b876c
Revises: 140b450225cd
Create Date: 2016-11-25 15:33:53.417103
"""

from __future__ import unicode_literals

from alembic import op

revision = "8990247b876c"
down_revision = "140b450225cd"


def upgrade():
    op.alter_column("group", "authority", nullable=False)


def downgrade():
    op.alter_column("group", "authority", nullable=True)
