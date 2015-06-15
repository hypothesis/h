# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy import func, and_

from h.db import Base


class Subscriptions(Base):
    __tablename__ = 'subscriptions'
    __table_args__ = sa.Index('subs_uri_idx_subscriptions', 'uri'),

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    uri = sa.Column(sa.Unicode(256), nullable=False)
    type = sa.Column(sa.VARCHAR(64), nullable=False)
    active = sa.Column(sa.BOOLEAN, default=True, nullable=False)

    @classmethod
    def get_by_id(cls, id):
        """Get a subscription by its primary key."""
        return cls.query.filter(cls.id == id).first()

    @classmethod
    def get_active_subscriptions_for_a_type(cls, ttype):
        return cls.query.filter(
            and_(
                cls.active,
                func.lower(cls.type) == func.lower(ttype)
            )
        ).all()

    @classmethod
    def get_subscriptions_for_uri(cls, uri):
        return cls.query.filter(
            func.lower(cls.uri) == func.lower(uri)
        ).all()

    @classmethod
    def get_templates_for_uri_and_type(cls, uri, ttype):
        return cls.query.filter(
            and_(
                func.lower(cls.uri) == func.lower(uri),
                func.lower(cls.type) == func.lower(ttype)
            )
        ).all()

    def __json__(self, request):
        return {'id': self.id,
                'uri': self.uri,
                'type': self.type,
                'active': self.active}


def includeme(_):
    pass
