"""
Add user profile columns

Revision ID: 6f86796f64e0
Revises: 7cf52a00822b
Create Date: 2016-07-06 11:28:50.075057
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa


revision = "6f86796f64e0"
down_revision = "7cf52a00822b"


def upgrade():
    op.add_column("user", sa.Column("display_name", sa.UnicodeText()))
    op.add_column("user", sa.Column("description", sa.UnicodeText()))
    op.add_column("user", sa.Column("location", sa.UnicodeText()))
    op.add_column("user", sa.Column("uri", sa.UnicodeText()))
    op.add_column("user", sa.Column("orcid", sa.UnicodeText()))


def downgrade():
    op.drop_column("user", "display_name")
    op.drop_column("user", "description")
    op.drop_column("user", "location")
    op.drop_column("user", "uri")
    op.drop_column("user", "orcid")
