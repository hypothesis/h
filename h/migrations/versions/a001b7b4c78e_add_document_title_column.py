"""
Add document title column

Revision ID: a001b7b4c78e
Revises: 94c989e06363
Create Date: 2016-09-12 11:59:35.296908
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa


revision = "a001b7b4c78e"
down_revision = "94c989e06363"


def upgrade():
    op.add_column("document", sa.Column("title", sa.UnicodeText()))


def downgrade():
    op.drop_column("document", "title")
