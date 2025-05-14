"""
Migrate DENIED -> SPAM.

At the time of this migration all annotations with a moderation_status
have "DENIED" coming from the hide feature.

Update those rows and the moderation_log ones to use SPAM instead.
"""

import sqlalchemy as sa
from alembic import op

revision = "ec5c9a864c76"
down_revision = "5831bc283ca9"


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
        WITH candidate_annotations as (
            -- These are all the old annotations hidden by the hide feature
            select annotation_id from annotation_moderation
            UNION
            -- These are all hidden annotations since the feature moved to the new style of storage
            select annotation_id from moderation_log
        )
        UPDATE annotation
        SET moderation_status = 'SPAM'
        FROM candidate_annotations
        WHERE candidate_annotations.annotation_id = annotation.id
        -- We only want to update annotations that are currently hidden
        AND annotation.moderation_status = 'DENIED'
    """
        )
    )
    print("\tUpdated annotation rows as SPAM:", result.rowcount)  # noqa: T201

    # We also want to update the moderation_log table
    # All current references to DENIED can be updated to SPAM
    conn.execute(
        sa.text(
            "UPDATE moderation_log SET new_moderation_status = 'SPAM' WHERE new_moderation_status = 'DENIED'"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE moderation_log SET old_moderation_status = 'SPAM' WHERE old_moderation_status = 'DENIED'"
        )
    )


def downgrade() -> None:
    pass
