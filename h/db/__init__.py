# -*- coding: utf-8 -*-

"""
Configure and expose the application database session.

This module is responsible for setting up the database session and engine, and
making that accessible to other parts of the application.

Models should inherit from `h.db.Base` in order to have their metadata bound at
application startup.

Most application code should access the database session using the request
property `request.db` which is provided by this module.
"""

import logging

import sqlalchemy
import zope.sqlalchemy
import zope.sqlalchemy.datamanager
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from h.util.session_tracker import Tracker

__all__ = (
    'Base',
    'Session',
    'init',
    'make_engine',
)

log = logging.getLogger(__name__)

# Create a default metadata object with naming conventions for indexes and
# constraints. This makes changing such constraints and indexes with alembic
# after creation much easier. See:
#
#   http://docs.sqlalchemy.org/en/latest/core/constraints.html#configuring-constraint-naming-conventions
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


def init(engine, base=Base, should_create=False, should_drop=False, authority=None):
    """Initialise the database tables managed by `h.db`."""
    # Import models package to populate the metadata
    import h.models  # noqa
    if should_drop:
        base.metadata.reflect(engine)
        base.metadata.drop_all(engine)
    if should_create:
        # In order to be able to generate UUIDs, we load the uuid-ossp
        # extension.
        engine.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        base.metadata.create_all(engine)

    _maybe_create_world_group(engine, authority)


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

    # Track uncommitted changes so we can verify that everything was either
    # committed or rolled back when the request finishes.
    db_session_checks = request.registry.settings.get('h.db_session_checks', True)
    if db_session_checks:
        tracker = Tracker(session)
    else:
        tracker = None

    # pyramid_tm doesn't always close the database session for us.
    #
    # For example if an exception view accesses the session and causes a new
    # transaction to be opened, pyramid_tm won't close this connection because
    # pyramid_tm's transaction has already ended before exception views are
    # executed.
    # Connections opened by NewResponse and finished callbacks aren't closed by
    # pyramid_tm either.
    #
    # So add our own callback here to make sure db sessions are always closed.
    #
    # See: https://github.com/Pylons/pyramid_tm/issues/40
    @request.add_finished_callback
    def close_the_sqlalchemy_session(request):
        changes = tracker.uncommitted_changes() if tracker else []
        if changes:
            msg = 'closing a session with uncommitted changes %s'
            log.warn(msg, changes, extra={
                'stack': True,
                'changes': changes,
            })
        session.close()

        # zope.sqlalchemy maintains an internal `id(session) => state` map with
        # an entry for each active DB session which is registered with it.
        #
        # Entries are normally cleared at the end of a request when the
        # transaction manager (`request.tm`) commits. DB writes after this can
        # leave stale entries in the map which can cause problems in future
        # requests if another session gets the same ID as the current one.
        dm = zope.sqlalchemy.datamanager
        if len(dm._SESSION_STATE) > 0:
            log.warn('request ended with non-empty zope.sqlalchemy state', extra={
                'data': {
                    'zope.sqlalchemy.datamanager._SESSION_STATE': dm._SESSION_STATE,
                },
            })
            dm._SESSION_STATE = {}

    return session


def _maybe_create_world_group(engine, authority):
    from h import models
    from h.models.group import ReadableBy, WriteableBy
    session = Session(bind=engine)
    world_group = session.query(models.Group).filter_by(pubid='__world__').one_or_none()
    if world_group is None:
        world_group = models.Group(name=u'Public',
                                   authority=authority,
                                   joinable_by=None,
                                   readable_by=ReadableBy.world,
                                   writeable_by=WriteableBy.authority)
        world_group.pubid = '__world__'
        session.add(world_group)

    session.commit()
    session.close()


def includeme(config):
    # Create the SQLAlchemy engine and save a reference in the app registry.
    engine = make_engine(config.registry.settings)
    config.registry['sqlalchemy.engine'] = engine

    # Add a property to all requests for easy access to the session. This means
    # that view functions need only refer to `request.db` in order to retrieve
    # the current database session.
    config.add_request_method(_session, name='db', reify=True)
