from functools import partial
from uuid import uuid1, uuid4, UUID

from annotator import annotation, document
from annotator.auth import DEFAULT_TTL

from horus.models import (
    get_session,
    BaseModel,
    ActivationMixin,
    GroupMixin,
    UserMixin,
    UserGroupMixin,
)

from pyramid.authentication import SessionAuthenticationPolicy

import transaction

from pyramid_basemodel import Base, Session

from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory(__package__)

from sqlalchemy import func, or_
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, TypeDecorator, CHAR, VARCHAR
from sqlalchemy.ext.declarative import declared_attr
import sqlalchemy as sa

try:
    import simplejson as json
except ImportError:
    import json

from h import interfaces, lib


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::

        JSONEncodedDict(255)

    """

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


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


class Annotation(annotation.Annotation):
    __mapping__ = {
        'annotator_schema_version': {'type': 'string'},
        'created': {'type': 'date'},
        'updated': {'type': 'date'},
        'quote': {'type': 'string'},
        'tags': {'type': 'string', 'index_name': 'not_analyzed'},
        'text': {'type': 'string'},
        'deleted': {'type': 'boolean'},
        'uri': {'type': 'string', 'index': 'not_analyzed'},
        'user': {'type': 'string', 'index': 'not_analyzed'},
        'consumer': {'type': 'string', 'index': 'not_analyzed'},
        'target': {
            'properties': {
                'id': {
                    'type': 'multi_field',
                    'path': 'just_name',
                    'fields': {
                        'id': {'type': 'string', 'index': 'not_analyzed'},
                        'uri': {'type': 'string', 'index': 'not_analyzed'},
                    },
                },
                'source': {
                    'type': 'multi_field',
                    'path': 'just_name',
                    'fields': {
                        'source': {'type': 'string', 'index': 'not_analyzed'},
                        'uri': {'type': 'string', 'index': 'not_analyzed'},
                    },
                },
                'selector': {
                    'properties': {
                        'type': {'type': 'string', 'index': 'no'},

                        # Annotator XPath+offset selector
                        'startContainer': {'type': 'string', 'index': 'no'},
                        'startOffset': {'type': 'long', 'index': 'no'},
                        'endContainer': {'type': 'string', 'index': 'no'},
                        'endOffset': {'type': 'long', 'index': 'no'},

                        # Open Annotation TextQuoteSelector
                        'exact': {
                            'type': 'multi_field',
                            'path': 'just_name',
                            'fields': {
                                'exact': {'type': 'string'},
                                'quote': {'type': 'string'},
                            },
                        },
                        'prefix': {'type': 'string'},
                        'suffix': {'type': 'string'},

                        # Open Annotation (Data|Text)PositionSelector
                        'start': {'type': 'long'},
                        'end':   {'type': 'long'},
                    }
                }
            }
        },
        'permissions': {
            'index_name': 'permission',
            'properties': {
                'read': {'type': 'string', 'index': 'not_analyzed'},
                'update': {'type': 'string', 'index': 'not_analyzed'},
                'delete': {'type': 'string', 'index': 'not_analyzed'},
                'admin': {'type': 'string', 'index': 'not_analyzed'}
            }
        },
        'references': {'type': 'string', 'index': 'not_analyzed'},
        'document': {
            'properties': document.MAPPING
        },
        'thread': {
            'type': 'string',
            'analyzer': 'thread'
        }
    }
    __settings__ = {
        'analysis': {
            'analyzer': {
                'thread': {
                    'tokenizer': 'path_hierarchy'
                }
            }
        }
    }

    @classmethod
    def update_settings(cls):
        cls.es.conn.indices.close(index=cls.es.index)
        try:
            cls.es.conn.indices.put_settings(
                index=cls.es.index,
                body=getattr(cls, '__settings__', {})
            )
        finally:
            cls.es.conn.indices.open(index=cls.es.index)


class Document(document.Document):
    pass


class ConsumerMixin(BaseModel):
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
        super(ConsumerMixin, self).__init__()
        self.__dict__.update(kwargs)

    def __repr__(self):
        return '<Consumer %r>' % self.key

    @classmethod
    def get_by_key(cls, key):
        return Session().query(cls).filter(cls.key == key).first()


class Activation(ActivationMixin, Base):
    pass


class Consumer(ConsumerMixin, Base):
    pass


class Group(GroupMixin, Base):
    pass


class User(UserMixin, Base):
    @declared_attr
    def subscriptions(self):
        return sa.Column(sa.BOOLEAN, nullable=False, default=False)

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


class UserSubscriptions(BaseModel, Base):
    @declared_attr
    def username(self):
        return sa.Column(
            sa.Unicode(30),
            sa.ForeignKey(
                '%s.%s' % (UserMixin.__tablename__, 'username'),
                onupdate='CASCADE',
                ondelete='CASCADE'
            ),
            nullable=False
        )

    @declared_attr
    def query(self):
        return sa.Column(JSONEncodedDict(4096), nullable=False)

    @declared_attr
    def template(self):
        return sa.Column(
            sa.Enum('reply_notification', 'custom_search',
                    name='subscription_template'),
            nullable=False,
            default='custom_search'
        )

    @declared_attr
    def description(self):
        return sa.Column(sa.VARCHAR(256), default="")

    @declared_attr
    def type(self):
        return sa.Column(
            sa.Enum('system', 'user', name='subscription_type'),
            nullable=False,
            default='user'
        )

    @declared_attr
    def active(self):
        return sa.Column(sa.BOOLEAN, default=True, nullable=False)


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

    authn_debug = config.registry.settings.get('pyramid.debug_authorization') \
        or config.registry.settings.get('debug_authorizations')
    authn_policy = SessionAuthenticationPolicy(
        callback=groupfinder,
        debug=authn_debug
    )
    config.set_authentication_policy(authn_policy)

    config.add_request_method(lib.user_property, 'user', property=True)

    if not registry.queryUtility(interfaces.IDBSession):
        registry.registerUtility(Session, interfaces.IDBSession)

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
