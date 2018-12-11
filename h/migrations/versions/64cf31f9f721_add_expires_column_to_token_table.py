"""
Add expires column to token table

Revision ID: 64cf31f9f721
Revises: d536d9a342f3
Create Date: 2016-08-15 15:45:21.813078
"""

from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op

revision = "64cf31f9f721"
down_revision = "d536d9a342f3"


def upgrade():
    op.add_column("token", sa.Column("expires", sa.DateTime, nullable=True))


def downgrade():
    op.drop_column("token", "expires")
