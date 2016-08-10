# -*- coding: utf-8 -*-

"""
Configure and expose the application database session.

This module is responsible for setting up the database session and engine, and
making that accessible to other parts of the application.

Models should inherit from `h.db.Base` in order to have their metadata bound at
application startup (and if `h.db.should_create_all` is set, their tables will
be automatically created).

Most application code should access the database session using the request
property `request.db` which is provided by this module.
"""

import sqlalchemy
import zope.sqlalchemy
from pyramid.settings import asbool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from memex import db as api_db

__all__ = (
    'Base',
    'Session',
    'init',
    'make_engine',
)

# Create a default metadata object with naming conventions for indexes and
# constraints. This makes changing such constraints and indexes with alembic
# after creation much easier. See:
#
#   http://docs.sqlalchemy.org/en/latest/core/constraints.html#configuring-constraint-naming-conventions
#
# N.B. This must be kept in sync with the naming conventions in
# :py:mod:`memex.db`.
#
metadata = sqlalchemy.MetaData(naming_convention={
    "ix": "ix__%(column_0_label)s",
    "uq": "uq__%(table_name)s__%(column_0_name)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "fk__%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
    "pk": "pk__%(table_name)s"
})

Base = declarative_base(metadata=metadata)

Session = sessionmaker()


def init(engine, base=Base, should_create=False, should_drop=False):
    """Initialise the database tables managed by `h.db`."""
    if should_drop:
        base.metadata.reflect(engine)
        base.metadata.drop_all(engine)
    if should_create:
        base.metadata.create_all(engine)
    api_db.init(engine, should_create=should_create, should_drop=should_drop)


def make_engine(settings):
    """Construct a sqlalchemy engine from the passed ``settings``."""
    return sqlalchemy.create_engine(settings['sqlalchemy.url'])


def _session(request):
    engine = request.registry['sqlalchemy.engine']
    session = Session(bind=engine)

    # If the request has a transaction manager, associate the session with it.
    try:
        tm = request.tm
    except AttributeError:
        pass
    else:
        zope.sqlalchemy.register(session, transaction_manager=tm)

    return session


def includeme(config):
    settings = config.registry.settings
    should_create = asbool(settings.get('h.db.should_create_all', False))
    should_drop = asbool(settings.get('h.db.should_drop_all', False))

    # Create the SQLAlchemy engine and save a reference in the app registry.
    engine = make_engine(settings)
    config.registry['sqlalchemy.engine'] = engine

    # Add a property to all requests for easy access to the session. This means
    # that view functions need only refer to `request.db` in order to retrieve
    # the current database session.
    config.add_request_method(_session, name='db', reify=True)

    # Register a deferred action to bind the engine when the configuration is
    # committed. Deferring the action means that this module can be included
    # before model modules without ill effect.
    config.action(None, init, (engine,), {
        'should_create': should_create,
        'should_drop': should_drop
    }, order=10)
