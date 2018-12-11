"""
Backfill group.authority

Revision ID: 140b450225cd
Revises: 3acf258322d5
Create Date: 2016-11-25 15:17:22.792448
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa

revision = "140b450225cd"
down_revision = "3acf258322d5"

group_table = sa.table("group", sa.Column("authority", sa.UnicodeText()))


def upgrade():
    op.execute(group_table.update().values(authority="hypothes.is"))


def downgrade():
    pass
