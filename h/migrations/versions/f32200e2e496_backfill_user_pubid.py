"""Backfill user.pubid with unique values."""

import logging
import random

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import declarative_base, sessionmaker

revision = "f32200e2e496"
down_revision = "3bae642f2b36"

logger = logging.getLogger(__name__)

USER_PUBID_LENGTH = 12
USER_BATCH_LIMIT = 1000
USER_MAX_COUNT = 100_000
USER_PUBID_RETRIES = 5


Base = declarative_base()


class User(Base):
    __tablename__ = "user"
    id = sa.Column(sa.Integer, primary_key=True)
    pubid = sa.Column(sa.String())


def generate(length):
    """
    Generate a random string of the specified length.

    This is the generate() function from h/pubid.py.
    """
    alphabet = "123456789ABDEGJKLMNPQRVWXYZabdegijkmnopqrvwxyz"
    return "".join(random.SystemRandom().choice(alphabet) for _ in range(length))


def backfill_users(
    session,
    user_batch_limit,
    user_max_count,
    user_pubid_retries,
    user_pubid_length,
):
    user_query = (
        session.query(User).filter(User.pubid.is_(None)).limit(user_batch_limit)
    )

    count = 0
    while users := user_query.all():
        if count >= user_max_count:
            logger.info("Reached maximum user count of %d", user_max_count)
            break
        batch_count = len(users)
        for retries in range(user_pubid_retries):
            try:
                for user in users:
                    user.pubid = generate(user_pubid_length)
                session.commit()
                count += batch_count
                break
            except sa.exc.IntegrityError:
                logger.warning(
                    "Failed to generate unique pubids, retrying %d/%d",
                    retries + 1,
                    USER_PUBID_RETRIES,
                )
                session.rollback()
        else:
            raise RuntimeError(f"Failed to generate {batch_count} unique pubids")

        logger.info("Back-filled %d user.pubid's", count)


def upgrade():
    session = sessionmaker()(bind=op.get_bind())

    backfill_users(
        session,
        user_batch_limit=USER_BATCH_LIMIT,
        user_max_count=USER_MAX_COUNT,
        user_pubid_retries=USER_PUBID_RETRIES,
        user_pubid_length=USER_PUBID_LENGTH,
    )


def downgrade():
    pass
