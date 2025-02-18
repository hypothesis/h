"""Create the notification table.

Revision ID: 372308320143
Revises: 7f9cbef8bb18
"""

import sqlalchemy as sa
from alembic import op

from h.db import types

revision = "372308320143"
down_revision = "7f9cbef8bb18"


def upgrade() -> None:
    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_annotation_id", types.URLSafeUUID(), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column(
            "notification_type",
            sa.Enum("MENTION", "REPLY", name="notificationtype"),
            nullable=False,
        ),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["source_annotation_id"],
            ["annotation.id"],
            name=op.f("fk__notification__source_annotation_id__annotation"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["user.id"],
            name=op.f("fk__notification__recipient_id__user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__notification")),
        sa.UniqueConstraint(
            "recipient_id",
            "source_annotation_id",
            name="uq__notification__recipient_id__source_annotation_id",
        ),
    )
    op.create_index(
        op.f("ix__notification_source_annotation_id"),
        "notification",
        ["source_annotation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__notification_recipient_id"),
        "notification",
        ["recipient_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix__notification_recipient_id"), table_name="notification")
    op.drop_index(
        op.f("ix__notification_source_annotation_id"), table_name="notification"
    )
    op.drop_table("notification")
    op.execute("DROP TYPE IF EXISTS notificationtype")
