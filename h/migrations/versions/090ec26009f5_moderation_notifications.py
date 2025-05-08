"""Moderation notifications."""

import sqlalchemy as sa
from alembic import op

revision = "090ec26009f5"
down_revision = "81a5daab8bfc"


def upgrade() -> None:
    op.drop_constraint(
        "uq__notification__recipient_id__source_annotation_id",
        "notification",
        type_="unique",
    )
    op.create_index(
        "ix__notification__recipient_id__source_annotation_id",
        "notification",
        ["recipient_id", "source_annotation_id"],
        unique=True,
        postgresql_where=sa.text("notification_type IN ('REPLY', 'MENTION')"),
    )
    op.execute(
        "ALTER TYPE notificationtype ADD VALUE 'ANNOTATION_MODERATED' AFTER 'REPLY'"
    )


def downgrade() -> None:
    op.drop_index(
        "ix__notification__recipient_id__source_annotation_id",
        table_name="notification",
        postgresql_where=sa.text("notification_type IN ('REPLY', 'MENTION')"),
    )
    op.create_unique_constraint(
        "uq__notification__recipient_id__source_annotation_id",
        "notification",
        ["recipient_id", "source_annotation_id"],
    )
