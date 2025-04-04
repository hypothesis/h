"""Backfill DENIED based on moderation."""

import sqlalchemy as sa
from alembic import op

revision = "96cde96b2fd7"
down_revision = "c8f748cbfb8f"


def upgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(
        sa.text(
            """
    UPDATE annotation
        SET moderation_status = 'DENIED'
    FROM annotation_moderation
    WHERE annotation.id = annotation_moderation.annotation_id
    AND annotation.moderation_status  is null
    """
        )
    )
    print("\tUpdated annotation rows as DENIED:", result.rowcount)  # noqa: T201

    result = conn.execute(
        sa.text(
            """
    UPDATE annotation_slim
        SET moderation_status = 'DENIED'
    FROM annotation_moderation
    WHERE annotation_slim.pubid = annotation_moderation.annotation_id
    AND annotation_slim.moderation_status is null
    """
        )
    )
    print("\tUpdated annotations as DENIED:", result.rowcount)  # noqa: T201


def downgrade() -> None:
    pass
