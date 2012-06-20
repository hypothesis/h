from datetime import datetime
from functools import partial
from uuid import uuid1, uuid4, UUID

from annotator.auth import DEFAULT_TTL

from apex import initialize_sql, groupfinder, RootFactory
from apex.models import AuthID, Base, DBSession

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.security import authenticated_userid

from sqlalchemy import engine_from_config
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.schema import Column
from sqlalchemy.types import DateTime, Integer, TypeDecorator, CHAR

class GUID(TypeDecorator):
    """Platform-independent GUID type.

    From http://docs.sqlalchemy.org/en/latest/core/types.html
    Copyright (C) 2005-2011 the SQLAlchemy authors and contributors

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(pg.UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, UUID):
                return "%.32x" % UUID(value)
            else:
                # hexstring
                return "%.32x" % value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return UUID(value)


class Consumer(Base):
    """API Consumer."""
    __tablename__ = 'consumers'

    key = Column(GUID, unique=True, primary_key=True)
    secret = Column(GUID, default=uuid4)
    ttl = Column(Integer, default=DEFAULT_TTL)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, key=partial(uuid1, clock_seq=id(Base))):
        self.key = key

    def __repr__(self):
        return '<Consumer %r>' % self.key

def includeme(config):
    config.include('pyramid_tm')
    config.set_request_property(lambda request: DBSession(), 'db', reify=True)
    config.set_request_property(
        lambda request: AuthID.get_by_id(authenticated_userid(request)),
        'user', reify=True)

    settings = config.registry.settings
    initialize_sql(engine_from_config(settings, 'sqlalchemy.'), settings)

    if not config.registry.queryUtility(IAuthorizationPolicy):
        authz_policy = ACLAuthorizationPolicy()
        config.set_authorization_policy(authz_policy)

    if not config.registry.queryUtility(IAuthenticationPolicy):
        auth_secret = settings['h.auth_secret']
        authn_policy = AuthTktAuthenticationPolicy(
            auth_secret, callback=groupfinder)
        config.set_authentication_policy(authn_policy)

    config.set_root_factory(RootFactory)
