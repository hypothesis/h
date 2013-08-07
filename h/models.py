from functools import partial
from uuid import uuid1, uuid4, UUID

from annotator.auth import DEFAULT_TTL

from hem.interfaces import IDBSession

from horus.models import (
    get_session,
    BaseModel,
    ActivationMixin,
    GroupMixin,
    UserMixin,
    UserGroupMixin,
)

import transaction

from pyramid_basemodel import Base, Session

from pyramid.i18n import TranslationStringFactory
_ = TranslationStringFactory(__package__)

from sqlalchemy import func, or_
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, TypeDecorator, CHAR

from h import interfaces, lib


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

    def python_type(self):
        return UUID


class Consumer(BaseModel, Base):
    """
    API Consumer

    The annotator-store :py:class:`annotator.auth.Authenticator` uses this
    function in the process of authenticating requests to verify the secrets of
    the JSON Web Token passed by the consumer client.

    """

    key = Column(GUID, default=partial(uuid1, clock_seq=id(Base)), index=True)
    secret = Column(GUID, default=uuid4)
    ttl = Column(Integer, default=DEFAULT_TTL)

    def __init__(self, **kwargs):
        super(Consumer, self).__init__()
        self.__dict__.update(kwargs)

    def __repr__(self):
        return '<Consumer %r>' % self.key

    @classmethod
    def get_by_key(cls, key):
        return Session().query(cls).filter(cls.key == key).first()


class Activation(ActivationMixin, Base):
    pass


class Group(GroupMixin, Base):
    pass


class User(UserMixin, Base):
    @classmethod
    def get_by_username(cls, request, username):
        session = get_session(request)

        lhs = func.replace(cls.username, '.', '')
        rhs = username.replace('.', '')
        return session.query(cls).filter(
            func.lower(lhs) == rhs.lower()
        ).first()

    @classmethod
    def get_by_username_or_email(cls, request, username, email):
        session = get_session(request)

        lhs = func.replace(cls.username, '.', '')
        rhs = username.replace('.', '')
        return session.query(cls).filter(
            or_(
                func.lower(lhs) == rhs.lower(),
                cls.email == email
            )
        ).first()


class UserGroup(UserGroupMixin, Base):
    pass


def groupfinder(userid, request):
    user = request.user
    groups = None
    if user:
        groups = []
        for group in user.groups:
            groups.append('group:%s' % group.name)
        groups.append('acct:%s@%s' % (user.username, request.server_name))
    return groups


def includeme(config):
    registry = config.registry
    config.include('pyramid_basemodel')
    config.include('pyramid_tm')

    config.set_request_property(lib.user_property, 'user')

    if not registry.queryUtility(IDBSession):
        registry.registerUtility(Session, IDBSession)

    if not registry.queryUtility(interfaces.IUserClass):
        registry.registerUtility(User, interfaces.IUserClass)

    if not registry.queryUtility(interfaces.IConsumerClass):
        registry.registerUtility(Consumer, interfaces.IConsumerClass)

    if not registry.queryUtility(interfaces.IActivationClass):
        registry.registerUtility(Activation, interfaces.IActivationClass)

    settings = config.get_settings()
    key = settings['api.key']
    secret = settings.get('api.secret')
    ttl = settings.get('api.ttl', DEFAULT_TTL)

    session = Session()
    with transaction.manager:
        consumer = Consumer.get_by_key(key)
        if not consumer:
            consumer = Consumer(key=key)
        consumer.secret = secret
        consumer.ttl = ttl
        session.add(consumer)
        session.flush()

    registry.consumer = consumer
