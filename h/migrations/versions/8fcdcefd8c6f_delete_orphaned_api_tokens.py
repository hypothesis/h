"""Delete orphaned API tokens."""

import logging

from alembic import op
from sqlalchemy import Column, Integer, UnicodeText, and_, delete, func, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "8fcdcefd8c6f"
down_revision = "8e04a443893d"


log = logging.getLogger(__name__)


Base = declarative_base()
Session = sessionmaker()


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(UnicodeText)
    authority = Column(UnicodeText)


class Token(Base):
    __tablename__ = "token"
    id = Column(Integer, primary_key=True)
    userid = Column(UnicodeText())


def upgrade():
    session = Session(bind=op.get_bind())

    userids = session.scalars(
        select(Token.userid)
        .outerjoin(
            User,
            and_(
                User.username
                == func.substring(func.split_part(Token.userid, "@", 1), 6),
                User.authority == func.split_part(Token.userid, "@", 2),
            ),
        )
        .where(User.id.is_(None))
        .distinct()
    ).all()

    op.execute(delete(Token).where(Token.userid.in_(userids)))
    log.info(f"Deleted %d orphaned tokens", len(userids))


def downgrade():
    pass
