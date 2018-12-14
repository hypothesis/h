"""
Remove NIPSA table

Revision ID: 53a74d7ae1b0
Revises: 1e88c31d8b1a
Create Date: 2016-09-20 12:12:03.600081
"""

from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op


revision = "53a74d7ae1b0"
down_revision = "1e88c31d8b1a"


def upgrade():
    op.drop_table("nipsa")


def downgrade():
    op.create_table("nipsa", sa.Column("userid", sa.UnicodeText, primary_key=True))
