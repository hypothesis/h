"""Create the moderation_status column."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c8f748cbfb8f"
down_revision = "cf4eedee60f7"


def upgrade() -> None:
    moderation_status_type = postgresql.ENUM(
        "APPROVED",
        "DENIED",
        "SPAM",
        "PRIVATE",
        "PENDING",
        name="moderationstatus",
    )
    moderation_status_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "annotation",
        sa.Column(
            "moderation_status",
            moderation_status_type,
            nullable=True,
        ),
    )
    op.add_column(
        "annotation_slim",
        sa.Column(
            "moderation_status",
            moderation_status_type,
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("annotation_slim", "moderation_status")
    op.drop_column("annotation", "moderation_status")
