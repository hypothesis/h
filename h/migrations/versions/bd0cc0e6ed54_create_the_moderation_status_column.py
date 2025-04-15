"""Create the moderation_status column."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "bd0cc0e6ed54"
down_revision = "1d26b96db4af"


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
        sa.Column("moderation_status", moderation_status_type, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("annotation", "moderation_status")
