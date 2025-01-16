"""Backfill user.pubid with unique values part 2."""

from alembic import op

from h.migrations.versions.f32200e2e496_backfill_user_pubid import backfill_users

revision = "f29f80083c26"
down_revision = "f32200e2e496"

USER_PUBID_LENGTH = 12
USER_BATCH_LIMIT = 1000
USER_MAX_COUNT = 1_000_000
USER_PUBID_RETRIES = 5


def upgrade():
    session = op.get_bind()

    backfill_users(
        session,
        USER_BATCH_LIMIT,
        USER_MAX_COUNT,
        USER_PUBID_RETRIES,
        USER_PUBID_LENGTH,
    )


def downgrade():
    pass
