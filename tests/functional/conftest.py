# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import contextlib
import os

import pytest
from webtest import TestApp

from h._compat import text_type
from tests.common.fixtures import es_client  # noqa: F401
from tests.common.fixtures import init_elasticsearch  # noqa: F401
from tests.common.fixtures.elasticsearch import ELASTICSEARCH_URL
from tests.common.fixtures.elasticsearch import ELASTICSEARCH_INDEX


TEST_SETTINGS = {
    "es.url": ELASTICSEARCH_URL,
    "es.index": ELASTICSEARCH_INDEX,
    "h.app_url": "http://example.com",
    "h.authority": "example.com",
    "pyramid.debug_all": False,
    "secret_key": "notasecret",
    "sqlalchemy.url": os.environ.get(
        "TEST_DATABASE_URL", "postgresql://postgres@localhost/htest"
    ),
}


@pytest.fixture
def app(pyramid_app, db_engine):
    from h import db

    _clean_database(db_engine)
    db.init(db_engine, authority=text_type(TEST_SETTINGS["h.authority"]))

    return TestApp(pyramid_app)


@pytest.fixture(scope="session")
def db_engine():
    from h import db

    engine = db.make_engine(TEST_SETTINGS)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Get a standalone database session for preparing database state."""
    from h import db

    session = db.Session(bind=db_engine)
    yield session
    session.close()


@pytest.fixture
def factories(db_session):
    from ..common import factories

    factories.set_session(db_session)
    yield factories
    factories.set_session(None)


@pytest.fixture(scope="session", autouse=True)
def init_db(db_engine):
    from h import db

    authority = text_type(TEST_SETTINGS["h.authority"])
    db.init(db_engine, should_drop=True, should_create=True, authority=authority)


@pytest.fixture(scope="session")
def pyramid_app():
    from h.app import create_app

    return create_app(None, **TEST_SETTINGS)


# Always unconditionally wipe the Elasticsearch index after every functional
# test.
@pytest.fixture(autouse=True)
def always_delete_all_elasticsearch_documents(es_client):  # noqa: F811
    pass


def _clean_database(engine):
    from h import db

    tables = reversed(db.Base.metadata.sorted_tables)
    with contextlib.closing(engine.connect()) as conn:
        tx = conn.begin()
        tnames = ", ".join('"' + t.name + '"' for t in tables)
        conn.execute("TRUNCATE {};".format(tnames))
        tx.commit()
