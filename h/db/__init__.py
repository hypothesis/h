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


DEFAULT_ORGANIZATION_LOGO = u"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
  <svg width="24px" height="28px" viewBox="0 0 24 28" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <rect fill="#ffffff" stroke="none" width="17.14407" height="16.046612" x="3.8855932" y="3.9449153" />
    <g id="Page-1" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
        <path d="M0,2.00494659 C0,0.897645164 0.897026226,0 2.00494659,0 L21.9950534,0 C23.1023548,0 24,0.897026226 24,2.00494659 L24,21.9950534 C24,23.1023548 23.1029738,24 21.9950534,24 L2.00494659,24 C0.897645164,24 0,23.1029738 0,21.9950534 L0,2.00494659 Z M9,24 L12,28 L15,24 L9,24 Z M7.00811294,4 L4,4 L4,20 L7.00811294,20 L7.00811294,15.0028975 C7.00811294,12.004636 8.16824717,12.0097227 9,12 C10,12.0072451 11.0189302,12.0606714 11.0189302,14.003477 L11.0189302,20 L14.0270431,20 L14.0270431,13.1087862 C14.0270433,10 12,9.00309038 10,9.00309064 C8.01081726,9.00309091 8,9.00309086 7.00811294,11.0019317 L7.00811294,4 Z M19,19.9869002 C20.1045695,19.9869002 21,19.0944022 21,17.9934501 C21,16.892498 20.1045695,16 19,16 C17.8954305,16 17,16.892498 17,17.9934501 C17,19.0944022 17.8954305,19.9869002 19,19.9869002 Z" id="Rectangle-2-Copy-17" fill="currentColor"></path>
    </g>
</svg>"""  # noqa: E501


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
    _maybe_create_default_organization(engine, authority)


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


def _maybe_create_default_organization(engine, authority):
    from h import models
    session = Session(bind=engine)
    default_org = session.query(models.Organization).filter_by(pubid='__default__').one_or_none()
    if default_org is None:
        default_org = models.Organization(name=u'Hypothesis',
                                          authority=authority,
                                          pubid='__default__',
                                          logo=DEFAULT_ORGANIZATION_LOGO,
                                          )
        session.add(default_org)

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
