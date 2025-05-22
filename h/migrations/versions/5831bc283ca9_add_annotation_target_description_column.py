"""Add the annotation.target_description column.

Revision ID: 5831bc283ca9
Revises: 81a5daab8bfc
"""

import sqlalchemy as sa
from alembic import op

revision = "5831bc283ca9"
down_revision = "81a5daab8bfc"


def upgrade():
    op.add_column("annotation", sa.Column("target_description", sa.UnicodeText))


def downgrade():
    op.drop_column("annotation", "target_description")
