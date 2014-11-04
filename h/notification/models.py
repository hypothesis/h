# -*- coding: utf-8 -*-
import logging
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func, and_

from pyramid_basemodel import Base
from hem.db import get_session
from horus.models import BaseModel

log = logging.getLogger(__name__)


class SubscriptionsMixin(BaseModel):
    # pylint: disable=no-self-use
    @declared_attr
    def __table_args__(self):
        return sa.Index('subs_uri_idx_%s' % self.__tablename__, 'uri'),

    @declared_attr
    def uri(self):
        return sa.Column(
            sa.Unicode(256),
            nullable=False
        )

    @declared_attr
    def template(self):
        return sa.Column(sa.VARCHAR(64), nullable=False)

    @declared_attr
    def active(self):
        return sa.Column(sa.BOOLEAN, default=True, nullable=False)

    @classmethod
    def get_active_subscriptions(cls, request):
        session = get_session(request)
        return session.query(cls).filter(cls.active).all()

    @classmethod
    def get_active_subscriptions_for_a_template(cls, request, template):
        session = get_session(request)
        return session.query(cls).filter(
            and_(
                cls.active,
                func.lower(cls.template) == func.lower(template)
            )
        ).all()

    @classmethod
    def get_subscriptions_for_uri(cls, request, uri):
        session = get_session(request)
        return session.query(cls).filter(
            func.lower(cls.uri) == func.lower(uri)
        ).all()

    @classmethod
    def get_a_template_for_uri(cls, request, uri, template):
        session = get_session(request)
        return session.query(cls).filter(
            and_(
                func.lower(cls.uri) == func.lower(uri),
                func.lower(cls.template) == func.lower(template)
            )
        ).all()


class Subscriptions(SubscriptionsMixin, Base):
    pass


def includeme(config):
    config.scan(__name__)
