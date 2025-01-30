"""Add username column to the mention table.

Revision ID: f59898e861be
Revises: 550865ed6622
"""

import sqlalchemy as sa
from alembic import op

revision = "f59898e861be"
down_revision = "550865ed6622"


def upgrade() -> None:
    op.add_column("mention", sa.Column("username", sa.UnicodeText(), nullable=False))


def downgrade() -> None:
    op.drop_column("mention", "username")
