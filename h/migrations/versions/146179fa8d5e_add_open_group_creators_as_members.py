"""Add open group creators as members."""

import enum
import logging
from collections import defaultdict

from alembic import op
from sqlalchemy import Column, Enum, ForeignKey, Integer, select
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

revision = "146179fa8d5e"
down_revision = "ecf91905c143"


log = logging.getLogger(__name__)


Base = declarative_base()


class JoinableBy(enum.Enum):
    pass


class ReadableBy(enum.Enum):
    world = "world"


class WriteableBy(enum.Enum):
    authority = "authority"


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)


class Group(Base):
    __tablename__ = "group"
    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey("user.id"))
    creator = relationship("User")
    joinable_by = Column(Enum(JoinableBy, name="group_joinable_by"))
    readable_by = Column(Enum(ReadableBy, name="group_readable_by"))
    writeable_by = Column(Enum(WriteableBy, name="group_writeable_by"))
    members = relationship("User", secondary="user_group")


class UserGroup(Base):
    __tablename__ = "user_group"
    id = Column(Integer, primary_key=True)
    user_id = Column("user_id", Integer, ForeignKey("user.id"))
    group_id = Column(Integer, ForeignKey("group.id"))


def upgrade():
    db = sessionmaker()(bind=op.get_bind())

    open_groups = db.scalars(
        select(Group)
        .where(Group.joinable_by == None)
        .where(Group.readable_by == ReadableBy.world)
        .where(Group.writeable_by == WriteableBy.authority)
    )

    results = defaultdict(lambda: 0)

    for group in open_groups:
        if not group.creator:
            results["no_creator"] += 1
        elif group.creator in group.members:
            results["already_member"] += 1
        else:
            group.members.append(group.creator)
            results["appended"] += 1

    db.commit()
    log.info(dict(results))


def downgrade():
    pass
