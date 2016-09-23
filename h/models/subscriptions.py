# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy import func

from h.db import Base


class Subscriptions(Base):
    __tablename__ = 'subscriptions'
    __table_args__ = sa.Index('subs_uri_idx_subscriptions', 'uri'),

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    uri = sa.Column(sa.UnicodeText(), nullable=False)
    type = sa.Column(sa.VARCHAR(64), nullable=False)
    active = sa.Column(sa.Boolean, default=True, nullable=False)

    @classmethod
    def get_subscriptions_for_uri(cls, session, uri):
        return session.query(cls).filter(
            func.lower(cls.uri) == func.lower(uri)
        ).all()

    def __repr__(self):
        return '<Subscription uri=%s type=%s active=%s>' % (self.uri,
                                                            self.type,
                                                            self.active)
