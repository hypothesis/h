"""
Disallow null annotation document_id

Revision ID: 5dce9a8c42c2
Revises: bcdd81e23920
Create Date: 2016-09-22 17:22:09.294825
"""

from __future__ import unicode_literals

from alembic import op


revision = "5dce9a8c42c2"
down_revision = "bcdd81e23920"


def upgrade():
    op.alter_column("annotation", "document_id", nullable=False)


def downgrade():
    op.alter_column("annotation", "document_id", nullable=True)
