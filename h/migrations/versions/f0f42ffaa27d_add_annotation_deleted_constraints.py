"""
Add constraints and defaults to annotation deleted column

Revision ID: f0f42ffaa27d
Revises: 9cbc5c5ad23d
Create Date: 2016-12-19 14:06:37.956780
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa


revision = "f0f42ffaa27d"
down_revision = "9cbc5c5ad23d"


def upgrade():
    op.alter_column(
        "annotation",
        "deleted",
        nullable=False,
        server_default=sa.sql.expression.false(),
    )


def downgrade():
    op.alter_column("annotation", "deleted", nullable=True, server_default=None)
