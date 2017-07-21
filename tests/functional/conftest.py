# -*- coding: utf-8 -*-

import contextlib
import os


import pytest
from webtest import TestApp

from h._compat import text_type


TEST_SETTINGS = {
    'es.host': os.environ.get('ELASTICSEARCH_HOST', 'http://localhost:9200'),
    'es.index': 'hypothesis-test',
    'h.app_url': 'http://example.com',
    'h.authority': 'example.com',
    'h.client_secret': 'notsosecret',
    'pyramid.debug_all': True,
    'sqlalchemy.url': os.environ.get('TEST_DATABASE_URL',
                                     'postgresql://postgres@localhost/htest')
}


@pytest.fixture
def app(pyramid_app, db_engine):
    from h import db

    _clean_database(db_engine)
    _clean_elasticsearch(TEST_SETTINGS)
    db.init(db_engine, authority=text_type(TEST_SETTINGS['h.authority']))

    return TestApp(pyramid_app)


@pytest.yield_fixture(scope='session')
def db_engine():
    from h import db
    engine = db.make_engine(TEST_SETTINGS)
    yield engine
    engine.dispose()


@pytest.yield_fixture
def db_session(db_engine):
    """Get a standalone database session for preparing database state."""
    from h import db
    session = db.Session(bind=db_engine)
    yield session
    session.close()


@pytest.yield_fixture
def factories(db_session):
    from ..common import factories
    factories.set_session(db_session)
    yield factories
    factories.set_session(None)


@pytest.fixture(scope='session', autouse=True)
def init_db(db_engine):
    from h import db
    authority = text_type(TEST_SETTINGS['h.authority'])
    db.init(db_engine, should_drop=True, should_create=True, authority=authority)


@pytest.fixture(scope='session', autouse=True)
def init_elasticsearch():
    from h.search import init, get_client
    client = get_client(TEST_SETTINGS)
    _drop_indices(TEST_SETTINGS)
    init(client)


@pytest.fixture(scope='session')
def pyramid_app():
    from h.app import create_app
    return create_app(None, **TEST_SETTINGS)


def _clean_database(engine):
    from h import db
    tables = reversed(db.Base.metadata.sorted_tables)
    with contextlib.closing(engine.connect()) as conn:
        tx = conn.begin()
        tnames = ', '.join('"' + t.name + '"' for t in tables)
        conn.execute('TRUNCATE {};'.format(tnames))
        tx.commit()


def _clean_elasticsearch(settings):
    import elasticsearch

    conn = elasticsearch.Elasticsearch([settings['es.host']])
    conn.delete_by_query(index=settings['es.index'],
                         body={"query": {"match_all": {}}})


def _drop_indices(settings):
    import elasticsearch

    conn = elasticsearch.Elasticsearch([settings['es.host']])

    name = settings['es.index']
    if conn.indices.exists(index=name):
        conn.indices.delete(index=name)
