"""Backfill moderation_status based on AnnotationModeration."""

import sqlalchemy as sa
from alembic import op

revision = "077e087027b1"
down_revision = "2aacaede8542"


def upgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(
        sa.text(
            """
    UPDATE annotation
        SET moderation_status = 'DENIED'
    FROM annotation_moderation
    WHERE annotation.id = annotation_moderation.annotation_id
    AND annotation.moderation_status is null
    """
        )
    )
    print("\tUpdated annotation rows as DENIED:", result.rowcount)  # noqa: T201


def downgrade() -> None:
    pass
