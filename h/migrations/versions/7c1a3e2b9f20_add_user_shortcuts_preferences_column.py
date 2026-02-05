"""Add user.shortcuts_preferences column."""

from alembic import op
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

revision = "7c1a3e2b9f20"
down_revision = "d4dd768e1439"


def upgrade():
    op.add_column("user", Column("shortcuts_preferences", JSONB, nullable=True))


def downgrade():
    op.drop_column("user", "shortcuts_preferences")
