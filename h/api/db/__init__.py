# -*- coding: utf-8 -*-

from annotator import es
from sqlalchemy import MetaData
from sqlalchemy.ext import declarative


# Create a default metadata object with naming conventions for indexes and
# constraints. This makes changing such constraints and indexes with alembic
# after creation much easier. See:
#
#   http://docs.sqlalchemy.org/en/latest/core/constraints.html#configuring-constraint-naming-conventions
#
# The migrations we run with alembic use the naming convention from
# :py:mod:`h.db`. In order that auto-created tables (i.e. those created by
# `Base.metadata.create_all()`) are compatible with these naming conventions,
# we need to specify them here, too, as `h.api` has its own global metadata
# object.
#
# N.B. This must be kept in sync with the naming conventions in :py:mod:`h.db`.
#
metadata = MetaData(naming_convention={
    "ix": "ix__%(column_0_label)s",
    "uq": "uq__%(table_name)s__%(column_0_name)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "fk__%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
    "pk": "pk__%(table_name)s"
})

Base = declarative.declarative_base(metadata=metadata)  # pylint: disable=invalid-name


def use_session(session, base=Base):
    """Configure the SQLAlchemy base class to use the given session."""
    base.query = session.query_property()


def bind_engine(engine, base=Base, should_create=False, should_drop=False):
    """Bind the SQLAlchemy base class to the given engine."""
    base.metadata.bind = engine
    if should_drop:
        base.metadata.drop_all(engine)
    if should_create:
        # In order to be able to generate UUIDs, we load the uuid-ossp
        # extension.
        engine.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        base.metadata.create_all(engine)


def includeme(config):
    """Configure Elasticsearch client."""
    settings = config.registry.settings

    if 'es.host' in settings:
        es.host = settings['es.host']

    if 'es.index' in settings:
        es.index = settings['es.index']

    if 'es.compatibility' in settings:
        es.compatibility_mode = settings['es.compatibility']
