"""Create moderation log table."""

import sqlalchemy as sa
from alembic import op

from h.db import types

revision = "bd226cc1c359"
down_revision = "96cde96b2fd7"


def upgrade() -> None:
    op.create_table(
        "moderation_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("annotation_id", types.URLSafeUUID(), nullable=False),
        sa.Column("old_moderation_status", sa.String(), nullable=False),
        sa.Column("new_moderation_status", sa.String(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["annotation_id"],
            ["annotation.id"],
            name=op.f("fk__moderation_log__annotation_id__annotation"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__moderation_log__user_id__user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__moderation_log")),
    )
    op.create_index(
        op.f("ix__moderation_log_annotation_id"),
        "moderation_log",
        ["annotation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("moderation_log")
    # ### end Alembic commands ###
