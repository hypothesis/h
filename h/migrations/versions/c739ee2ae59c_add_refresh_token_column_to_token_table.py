"""
add refresh_token column to token table

Revision ID: c739ee2ae59c
Revises: 9f5e274b202c
Create Date: 2017-01-24 19:00:07.493002
"""

from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op


revision = "c739ee2ae59c"
down_revision = "9f5e274b202c"


def upgrade():
    op.add_column("token", sa.Column("refresh_token", sa.UnicodeText, nullable=True))


def downgrade():
    op.drop_column("token", "refresh_token")
