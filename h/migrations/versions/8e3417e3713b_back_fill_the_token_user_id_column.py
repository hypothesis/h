"""Back-fill the token.user_id column."""

import logging
import re

from alembic import op
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from h.models import Token, User

revision = "8e3417e3713b"
down_revision = "8fcdcefd8c6f"


log = logging.getLogger(__name__)


def split_userid(userid):
    return re.match(r"^acct:([^@]+)@(.*)$", userid).groups()


def upgrade():
    session = sessionmaker()(bind=op.get_bind())

    tokens_query = select(Token).where(Token.user_id.is_(None)).limit(1000)
    count = 0

    while tokens := session.scalars(tokens_query).all():
        for token in tokens:
            username, authority = split_userid(token.userid)
            token.user_id = session.scalars(
                select(User.id).where(
                    User.username == username, User.authority == authority
                )
            ).one()
            count += 1
        session.commit()
        log.info("Back-filled %d token.user_id's", count)


def downgrade():
    pass
