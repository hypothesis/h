"""Back-fill the token.user_id column."""

import logging
import re

from alembic import op
from sqlalchemy import Column, ForeignKey, Integer, UnicodeText, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "8e3417e3713b"
down_revision = "8fcdcefd8c6f"


log = logging.getLogger(__name__)


Base = declarative_base()


class Token(Base):
    __tablename__ = "token"

    id = Column(Integer, primary_key=True)

    # Legacy `userid` column.
    userid = Column(UnicodeText())

    # Replacement foreign key.
    user_id = Column(Integer, ForeignKey("user.id"))


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(UnicodeText(), nullable=False)
    authority = Column(UnicodeText(), nullable=False)


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
