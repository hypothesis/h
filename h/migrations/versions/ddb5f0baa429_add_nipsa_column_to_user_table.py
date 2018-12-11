"""
Add NIPSA column to user table

Revision ID: ddb5f0baa429
Revises: 6d9257ad610d
Create Date: 2016-09-16 16:58:03.585538
"""

from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op


revision = "ddb5f0baa429"
down_revision = "6d9257ad610d"


def upgrade():
    op.add_column("user", sa.Column("nipsa", sa.Boolean, nullable=True))


def downgrade():
    op.drop_column("user", "nipsa")
