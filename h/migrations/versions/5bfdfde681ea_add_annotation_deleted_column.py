"""
Add annotation deleted column

Revision ID: 5bfdfde681ea
Revises: 90412d879d1f
Create Date: 2016-12-19 12:37:53.791428
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa


revision = "5bfdfde681ea"
down_revision = "90412d879d1f"


def upgrade():
    op.add_column(
        "annotation", sa.Column("deleted", sa.Boolean, nullable=True, index=True)
    )


def downgrade():
    op.drop_column("annotation", "deleted")
