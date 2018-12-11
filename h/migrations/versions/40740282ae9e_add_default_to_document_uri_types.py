"""
Add default to document_uri type fields

Revision ID: 40740282ae9e
Revises: 296575bb30b3
Create Date: 2016-06-29 11:01:40.936313
"""

from __future__ import unicode_literals

revision = "40740282ae9e"
down_revision = "296573bb30b3"

from alembic import op


def upgrade():
    op.alter_column("document_uri", "type", server_default="")
    op.alter_column("document_uri", "content_type", server_default="")


def downgrade():
    op.alter_column("document_uri", "type", server_default=None)
    op.alter_column("document_uri", "content_type", server_default=None)
