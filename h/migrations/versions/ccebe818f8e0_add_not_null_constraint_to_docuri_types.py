"""
Add NOT NULL constraint to document_uri type fields

Revision ID: ccebe818f8e0
Revises: 467ea2898660
Create Date: 2016-06-29 10:57:37.466053
"""

from __future__ import unicode_literals

revision = "ccebe818f8e0"
down_revision = "467ea2898660"

from alembic import op


def upgrade():
    op.alter_column("document_uri", "type", nullable=False)
    op.alter_column("document_uri", "content_type", nullable=False)


def downgrade():
    op.alter_column("document_uri", "type", nullable=True)
    op.alter_column("document_uri", "content_type", nullable=True)
