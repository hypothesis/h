# pylint: disable=import-outside-toplevel, cyclic-import
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
from os import environ

import sqlalchemy
import zope.sqlalchemy
import zope.sqlalchemy.datamanager
from sqlalchemy import text
from sqlalchemy.orm import declarative_base, sessionmaker

__all__ = ("Base", "Session", "pre_create", "post_create", "create_engine")

log = logging.getLogger(__name__)

# Create a default metadata object with naming conventions for indexes and
# constraints. This makes changing such constraints and indexes with alembic
# after creation much easier. See:
#
#   http://docs.sqlalchemy.org/en/latest/core/constraints.html#configuring-constraint-naming-conventions
#
metadata = sqlalchemy.MetaData(
    naming_convention={
        "ix": "ix__%(column_0_label)s",
        "uq": "uq__%(table_name)s__%(column_0_name)s",
        "ck": "ck__%(table_name)s__%(constraint_name)s",
        "fk": "fk__%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
        "pk": "pk__%(table_name)s",
    }
)

Base = declarative_base(metadata=metadata)

Session = sessionmaker()


def pre_delete(engine):  # pragma: no cover
    with engine.connect() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS report CASCADE"))
        connection.commit()


def pre_create(engine):  # pragma: no cover
    with engine.connect() as connection:
        connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        connection.commit()


def post_create(engine):  # pragma: no cover
    authority = environ["AUTHORITY"]

    default_org = _maybe_create_default_organization(engine, authority)
    _maybe_create_world_group(engine, authority, default_org)


def create_engine(database_url):  # pragma: no cover
    """Construct a sqlalchemy engine from the passed ``settings``."""
    return sqlalchemy.create_engine(database_url)


def _session(request):  # pragma: no cover
    engine = request.registry["sqlalchemy.engine"]
    session = Session(bind=engine)

    # If the request has a transaction manager, associate the session with it.
    try:
        tm = request.tm
    except AttributeError:
        pass
    else:
        zope.sqlalchemy.register(session, transaction_manager=tm)

    # pyramid_tm doesn't always close the database session for us.
    #
    # If anything that executes later in the Pyramid request processing cycle
    # than pyramid_tm tween egress opens a new DB session (for example a tween
    # above the pyramid_tm tween, a response callback, or a NewResponse
    # subscriber) then pyramid_tm won't close that DB session for us.
    #
    # So as a precaution add our own callback here to make sure db sessions are
    # always closed.
    @request.add_finished_callback
    def close_the_sqlalchemy_session(_request):
        # Close any unclosed DB connections.
        # It's okay to call `session.close()` even if the session does not need to
        # be closed, so just call it so that there's no chance
        # of leaking any unclosed DB connections.
        session.close()

    return session


def _replica_session(request):  # pragma: no cover
    engine = create_engine(request.registry.settings["sqlalchemy.replica.url"])
    session = Session(bind=engine)

    # While this is superflux when using a real replica it guarantees that usage of request.db_replica
    # in the codebase never expects to be able to write to the DB, useful on the dev and tests environments.
    session.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;"))

    @request.add_finished_callback
    def close_the_sqlalchemy_session(_request):
        # Close any unclosed DB connections.
        # It's okay to call `session.close()` even if the session does not need to
        # be closed, so just call it so that there's no chance
        # of leaking any unclosed DB connections.
        session.close()

    return session


def _maybe_create_default_organization(engine, authority):  # pragma: no cover
    from h.services.organization import OrganizationService

    session = Session(bind=engine)
    default_org = OrganizationService(session).get_default(authority)

    session.commit()
    session.close()

    return default_org


def _maybe_create_world_group(engine, authority, default_org):  # pragma: no cover
    from h import models
    from h.models.group import ReadableBy, WriteableBy

    session = Session(bind=engine)
    world_group = session.query(models.Group).filter_by(pubid="__world__").one_or_none()
    if world_group is None:  # pragma: no cover
        world_group = models.Group(
            name="Public",
            authority=authority,
            joinable_by=None,
            readable_by=ReadableBy.world,
            writeable_by=WriteableBy.authority,
            organization=default_org,
        )
        world_group.pubid = "__world__"
        session.add(world_group)

    session.commit()
    session.close()


def includeme(config):  # pragma: no cover
    # Create the SQLAlchemy engine and save a reference in the app registry.
    engine = create_engine(config.registry.settings["sqlalchemy.url"])
    config.registry["sqlalchemy.engine"] = engine

    # Add a property to all requests for easy access to the session. This means
    # that view functions need only refer to `request.db` in order to retrieve
    # the current database session.
    config.add_request_method(_session, name="db", reify=True)
    config.add_request_method(_replica_session, name="db_replica", reify=True)
