"""Remove old tokens."""

import logging

from alembic import op
from sqlalchemy import TIMESTAMP, Column, DateTime, ForeignKey, Integer, delete, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "9e47da806421"
down_revision = "36459b033a54"


log = logging.getLogger(__name__)


Base = declarative_base()


class Token(Base):
    __tablename__ = "token"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    created = Column(DateTime)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    registered_date = Column(TIMESTAMP(timezone=False))


def upgrade():
    session = sessionmaker()(bind=op.get_bind())
    count = 0

    while True:
        deleted_token_ids = session.scalars(
            delete(Token)
            .where(
                Token.id.in_(
                    select(
                        select(Token.id)
                        .join(User)
                        .where(Token.created < User.registered_date)
                        .limit(1000)
                        .cte()
                    )
                )
            )
            .returning(Token.id)
        ).all()

        if not deleted_token_ids:
            break

        for deleted_token_id in deleted_token_ids:
            count += 1
            log.info(f"Deleted token (%d): %s", count, deleted_token_id)


def downgrade():
    pass
