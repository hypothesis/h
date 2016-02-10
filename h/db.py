# -*- coding: utf-8 -*-

"""
Configure and expose the application database session.

This module is responsible for setting up the database session and engine, and
making that accessible to other parts of the application.

Models should inherit from `h.db.Base` in order to have their metadata bound at
application startup (and if `h.db.should_create_all` is set, their tables will
be automatically created).

Access to the database session can either be through the `h.db.Session` session
factory, or through the request property `request.db` which is provided by this
module.
"""

from pyramid.settings import asbool
from sqlalchemy import MetaData
from sqlalchemy import engine_from_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from zope.sqlalchemy import ZopeTransactionExtension

from h.api import db as api_db

__all__ = (
    'Base',
    'Session',
    'bind_engine',
    'make_engine',
)

# Create a thread-local session factory (which can also be used directly as a
# session):
#
#   http://docs.sqlalchemy.org/en/latest/orm/contextual.html#using-thread-local-scope-with-web-applications
#
# Using ZopeTransactionExtension from zope.sqlalchemy ensures that sessions are
# correctly scoped to the current processing request, and that sessions are
# automatically committed (or aborted) when the request terminates. This
# integration with pyramid is provided by `pyramid_tm`:
#
#   http://docs.pylonsproject.org/projects/pyramid-tm/en/latest/#transaction-usage
#
Session = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

# Create a default metadata object with naming conventions for indexes and
# constraints. This makes changing such constraints and indexes with alembic
# after creation much easier. See:
#
#   http://docs.sqlalchemy.org/en/latest/core/constraints.html#configuring-constraint-naming-conventions
#
# N.B. This must be kept in sync with the naming conventions in
# :py:mod:`h.api.db`.
#
metadata = MetaData(naming_convention={
    "ix": "ix__%(column_0_label)s",
    "uq": "uq__%(table_name)s__%(column_0_name)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "fk__%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
    "pk": "pk__%(table_name)s"
})


# Provide a very simple base class with a dynamic query property.
class _Base(object):
    query = Session.query_property()

Base = declarative_base(cls=_Base, metadata=metadata)


def bind_engine(engine,
                session=Session,
                base=Base,
                should_create=False,
                should_drop=False):
    """Bind the ``session`` and ``base`` to the ``engine``."""
    session.configure(bind=engine)
    base.metadata.bind = engine
    if should_drop:
        base.metadata.reflect(engine)
        base.metadata.drop_all(engine)
    if should_create:
        base.metadata.create_all(engine)
    api_db.bind_engine(engine, should_create=should_create,
                       should_drop=should_drop)


def make_engine(settings):
    """Construct a sqlalchemy engine from the passed ``settings``."""
    return engine_from_config(settings, 'sqlalchemy.')


def includeme(config):
    settings = config.registry.settings
    should_create = asbool(settings.get('h.db.should_create_all', False))
    should_drop = asbool(settings.get('h.db.should_drop_all', False))
    engine = make_engine(settings)

    # Add a property to all requests for easy access to the session. This means
    # that view functions need only refer to `request.db` in order to retrieve
    # the current database session.
    config.add_request_method(lambda req: Session(), name='db', reify=True)

    # Register a deferred action to bind the engine when the configuration is
    # committed. Deferring the action means that this module can be included
    # before model modules without ill effect.
    config.action(None, bind_engine, (engine,), {
        'should_create': should_create,
        'should_drop': should_drop
    }, order=10)

    api_db.use_session(Session)
