"""
Fill in user authority column.

Revision ID: 2e2cc6a0c521
Revises: f48100c9af86
Create Date: 2016-08-15 18:13:08.372479
"""

import sqlalchemy as sa
from alembic import op

revision = "2e2cc6a0c521"
down_revision = "f48100c9af86"

user_table = sa.table("user", sa.Column("authority", sa.UnicodeText()))


def upgrade():
    op.execute(user_table.update().values(authority="hypothes.is"))


def downgrade():
    pass
