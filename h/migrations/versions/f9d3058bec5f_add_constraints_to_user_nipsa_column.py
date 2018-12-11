"""
Add constraints to user NIPSA column

Revision ID: f9d3058bec5f
Revises: b7117b569f8b
Create Date: 2016-09-19 13:07:58.098068
"""

from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op


revision = "f9d3058bec5f"
down_revision = "b7117b569f8b"


def upgrade():
    op.alter_column("user", "nipsa", nullable=False)
    op.alter_column("user", "nipsa", server_default=sa.sql.expression.false())


def downgrade():
    op.alter_column("user", "nipsa", nullable=True)
    op.alter_column("user", "nipsa", server_default=None)
