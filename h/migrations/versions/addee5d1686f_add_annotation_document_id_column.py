"""
Add annotation document_id column

Revision ID: addee5d1686f
Revises: 63e8b1fe1d4b
Create Date: 2016-09-22 15:55:06.069829
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa


revision = "addee5d1686f"
down_revision = "63e8b1fe1d4b"


def upgrade():
    op.add_column(
        "annotation",
        sa.Column(
            "document_id",
            sa.Integer,
            sa.ForeignKey("document.id"),
            nullable=True,
            index=True,
        ),
    )


def downgrade():
    op.drop_column("annotation", "document_id")
