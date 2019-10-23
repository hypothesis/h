"""
Add authority column to group

Revision ID: 3acf258322d5
Revises: c36369fe730f
Create Date: 2016-11-24 16:33:40.238726
"""

import sqlalchemy as sa
from alembic import op

revision = "3acf258322d5"
down_revision = "c36369fe730f"


def upgrade():
    op.add_column("group", sa.Column("authority", sa.UnicodeText(), nullable=True))


def downgrade():
    op.drop_column("group", "authority")
