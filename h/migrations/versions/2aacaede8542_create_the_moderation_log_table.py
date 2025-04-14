"""Create the moderation log table."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from h.db.types import URLSafeUUID

revision = "2aacaede8542"
down_revision = "bd0cc0e6ed54"


def upgrade() -> None:
    moderation_status_type = postgresql.ENUM(
        name="moderationstatus",
        create_type=False,
    )

    op.create_table(
        "moderation_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("moderator_id", sa.Integer(), nullable=False),
        sa.Column("annotation_id", URLSafeUUID(), nullable=False),
        sa.Column("old_moderation_status", moderation_status_type, nullable=True),
        sa.Column("new_moderation_status", moderation_status_type, nullable=False),
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
            ["moderator_id"],
            ["user.id"],
            name=op.f("fk__moderation_log__moderator_id_user"),
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
    op.drop_index(op.f("ix__moderation_log_annotation_id"), table_name="moderation_log")
    op.drop_table("moderation_log")
