"""Allow null moderator_id on ModerationLog."""

import sqlalchemy as sa
from alembic import op

revision = "81a5daab8bfc"
down_revision = "077e087027b1"


def upgrade() -> None:
    op.alter_column(
        "moderation_log", "moderator_id", existing_type=sa.INTEGER(), nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "moderation_log", "moderator_id", existing_type=sa.INTEGER(), nullable=False
    )
