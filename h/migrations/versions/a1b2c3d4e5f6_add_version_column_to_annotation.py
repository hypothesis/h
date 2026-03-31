"""Add version column to annotation table."""

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "1d93a1310f5d"


def upgrade() -> None:
    op.add_column("annotation", sa.Column("version", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("annotation", "version")
