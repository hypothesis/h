"""Backfill user.pubid with unique values part 4."""

from alembic import op
from sqlalchemy.orm import sessionmaker

from h.migrations.versions.f32200e2e496_backfill_user_pubid import backfill_users

revision = "01c9594fb9d5"
down_revision = "9b7171cdeb8a"

USER_PUBID_LENGTH = 12
USER_BATCH_LIMIT = 1000
USER_MAX_COUNT = 3_000_000
USER_PUBID_RETRIES = 5


def upgrade():
    session = sessionmaker()(bind=op.get_bind())

    backfill_users(
        session,
        USER_BATCH_LIMIT,
        USER_MAX_COUNT,
        USER_PUBID_RETRIES,
        USER_PUBID_LENGTH,
    )


def downgrade():
    pass
