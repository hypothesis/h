"""Add token.user_id column."""

from alembic import op
from sqlalchemy import Column, ForeignKey, Integer

revision = "8f5b6f8bbba8"
down_revision = "aeda42d241b3"


def upgrade():
    op.add_column(
        "token",
        Column(
            "user_id",
            Integer,
            ForeignKey("user.id", ondelete="cascade"),
            index=True,
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("token", "user_id")
