"""Add username column to mention table.

Revision ID: bfc54f0844aa
Revises: 39cc1025a3a2
"""

import sqlalchemy as sa
from alembic import op

revision = "bfc54f0844aa"
down_revision = "39cc1025a3a2"


def upgrade() -> None:
    op.add_column("mention", sa.Column("username", sa.UnicodeText(), nullable=False))


def downgrade() -> None:
    op.drop_column("mention", "username")
