# -*- coding: utf-8 -*-

from annotator import es
from sqlalchemy.ext import declarative


Base = declarative.declarative_base()  # pylint: disable=invalid-name


def use_session(session, base=Base):
    """Configure the SQLAlchemy base class to use the given session."""
    base.query = session.query_property()


def bind_engine(engine, base=Base, should_create=False, should_drop=False):
    """Bind the SQLAlchemy base class to the given engine."""
    base.metadata.bind = engine
    if should_drop:
        base.metadata.drop_all(engine)
    if should_create:
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
