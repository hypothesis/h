"""Moderation log notifications."""

import sqlalchemy as sa
from alembic import op

revision = "017cae80ccb7"
down_revision = "090ec26009f5"


def upgrade() -> None:
    op.add_column(
        "moderation_log", sa.Column("notification_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk__moderation_log__notification_id__notification"),
        "moderation_log",
        "notification",
        ["notification_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk__moderation_log__notification_id__notification"),
        "moderation_log",
        type_="foreignkey",
    )
    op.drop_column("moderation_log", "notification_id")
