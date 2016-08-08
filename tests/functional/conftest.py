# -*- coding: utf-8 -*-

import os

import pytest
from webtest import TestApp


TEST_SETTINGS = {
    'es.host': os.environ.get('ELASTICSEARCH_HOST', 'http://localhost:9200'),
    'es.index': 'hypothesis-test',
    'h.app_url': 'http://localhost',
    'h.db.should_create_all': True,
    'h.db.should_drop_all': True,
    'h.search.autoconfig': True,
    'pyramid.debug_all': True,
    'sqlalchemy.url': os.environ.get('TEST_DATABASE_URL',
                                     'postgresql://postgres@localhost/htest')
}


@pytest.fixture
def config():
    from h.config import configure

    config = configure()
    config.registry.settings.update(TEST_SETTINGS)
    _drop_indices(settings=config.registry.settings)
    config.include('h.app')
    config.include('h.session')
    return config


@pytest.fixture
def app(config):
    return TestApp(config.make_wsgi_app())


@pytest.yield_fixture
def db_session(request, config):
    """Get a standalone database session for preparing database state."""
    from h import db
    engine = db.make_engine(config.registry.settings)
    session = db.Session(bind=engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.yield_fixture
def factories(db_session):
    from ..common import factories
    factories.SESSION = db_session
    yield factories
    factories.SESSION = None


def _drop_indices(settings):
    import elasticsearch

    conn = elasticsearch.Elasticsearch([settings['es.host']])

    name = settings['es.index']
    if conn.indices.exists(index=name):
        conn.indices.delete(index=name)
