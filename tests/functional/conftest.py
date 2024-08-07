import contextlib
import os

import pytest
from sqlalchemy import text
from webtest import TestApp

from h import db
from h.app import create_app
from tests.common import factories as factories_common
from tests.common.fixtures.elasticsearch import (  # pylint: disable=unused-import
    ELASTICSEARCH_INDEX,
    ELASTICSEARCH_URL,
    es_client,
    init_elasticsearch,
)
from tests.functional.fixtures.authentication import *  # pylint:disable=wildcard-import,unused-wildcard-import
from tests.functional.fixtures.groups import *  # pylint:disable=wildcard-import,unused-wildcard-import

TEST_SETTINGS = {
    "es.url": ELASTICSEARCH_URL,
    "es.index": ELASTICSEARCH_INDEX,
    "h.app_url": "http://example.com",
    "h.authority": "example.com",
    "h.sentry_dsn_frontend": "TEST_SENTRY_DSN_FRONTEND",
    "pyramid.debug_all": False,
    "secret_key": "notasecret",
    "h_api_auth_cookie_secret_key": b"test_h_api_auth_cookie_secret_key",
    "h_api_auth_cookie_salt": b"test_h_api_auth_cookie_salt",
    "sqlalchemy.url": os.environ["DATABASE_URL"],
}

TEST_ENVIRONMENT = {
    "ELASTICSEARCH_URL": TEST_SETTINGS["es.url"],
    "ELASTICSEARCH_INDEX": TEST_SETTINGS["es.index"],
    "APP_URL": TEST_SETTINGS["h.app_url"],
    "AUTH_DOMAIN": TEST_SETTINGS["h.authority"],
    "SENTRY_DSN_FRONTEND": TEST_SETTINGS["h.sentry_dsn_frontend"],
    "SECRET_KEY": TEST_SETTINGS["secret_key"],
    "H_API_AUTH_COOKIE_SECRET_KEY": TEST_SETTINGS["h_api_auth_cookie_secret_key"],
    "H_API_AUTH_COOKIE_SALT": TEST_SETTINGS["h_api_auth_cookie_salt"],
    "DATABASE_URL": TEST_SETTINGS["sqlalchemy.url"],
}


@pytest.fixture(scope="session")
def app(pyramid_app):
    return TestApp(pyramid_app)


@pytest.fixture(autouse=True)
def reset_app(app):
    yield

    app.reset()


@pytest.fixture
def with_clean_db(db_engine):
    tables = reversed(db.Base.metadata.sorted_tables)
    with contextlib.closing(db_engine.connect()) as conn:
        tx = conn.begin()
        tnames = ", ".join('"' + t.name + '"' for t in tables)
        conn.execute(text(f"TRUNCATE {tnames};"))
        tx.commit()

    # We need to re-init the DB as it creates the default test group and
    # possibly more in future?
    db.pre_create(db_engine)
    db.Base.metadata.create_all(db_engine)
    db.post_create(db_engine)


@pytest.fixture
def db_session(db_engine, db_sessionfactory):
    """Get a standalone database session for preparing database state."""
    session = db_sessionfactory(bind=db_engine)
    yield session
    session.close()


@pytest.fixture
def factories(db_session):
    factories_common.set_session(db_session)
    yield factories_common
    factories_common.set_session(None)


@pytest.fixture(scope="session")
def pyramid_app():
    return create_app(None, **TEST_SETTINGS)


# Always unconditionally wipe the Elasticsearch index after every functional
# test.
@pytest.fixture(autouse=True)
def always_delete_all_elasticsearch_documents():
    pass
