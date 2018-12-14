"""
Add authority column to user table

Revision ID: f48100c9af86
Revises: 64cf31f9f721
Create Date: 2016-08-15 18:10:23.511861
"""

from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op


revision = "f48100c9af86"
down_revision = "64cf31f9f721"


def upgrade():
    op.add_column("user", sa.Column("authority", sa.UnicodeText(), nullable=True))


def downgrade():
    op.drop_column("user", "authority")
