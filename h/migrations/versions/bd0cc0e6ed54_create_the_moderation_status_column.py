"""Create the moderation_status column."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "bd0cc0e6ed54"
down_revision = "9d97a3e4921e"


def upgrade() -> None:
    moderation_status_type = postgresql.ENUM(
        "APPROVED",
        "DENIED",
        "SPAM",
        "PENDING",
        name="moderationstatus",
    )
    moderation_status_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "annotation",
        sa.Column(
            "moderation_status",
            sa.Enum("APPROVED", "PENDING", "DENIED", "SPAM", name="moderationstatus"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("annotation", "moderation_status")
