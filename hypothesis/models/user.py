from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from . import Base

__all__ = ['User']

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(128), unique=True)
    password_hash = Column(String(128))

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    @classmethod
    def fetch(cls, id):
        return cls.query.filter_by(id=id).first()

    def __init__(self, username, password=None):
        self.username = username
        if password:
            self.password = password

    def __repr__(self):
        return '<User %r>' % self.username

    def _password_set(self, v):
        # TODO: bcrypt + salt from config
        pass

    password = property(None, _password_set)

    def check_password(self, password):
        if not self.password_hash:
            return False
        raise NotImplemented
