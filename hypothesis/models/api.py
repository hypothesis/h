from datetime import datetime
from functools import partial
from uuid import uuid1, uuid4

from annotator import auth

from sqlalchemy.schema import Column
from sqlalchemy.types import DateTime, Integer

from . import Base, DBSession
from . types import GUID

class Consumer(Base):
    __tablename__ = 'consumers'

    key = Column(GUID, unique=True, primary_key=True)
    secret = Column(GUID, default=uuid4)
    ttl = Column(Integer, default=auth.DEFAULT_TTL)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, key=partial(uuid1, clock_seq=id(Base))):
        self.key = key

    def __repr__(self):
        return '<Consumer %r>' % self.key
