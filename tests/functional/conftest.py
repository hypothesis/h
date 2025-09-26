import contextlib
import os

import elasticsearch.exceptions
import pytest
from sqlalchemy import text
from webtest import TestApp

from h import db
from h.app import create_app
from tests.common import factories as factories_common
from tests.functional.fixtures.authentication import *  # noqa: F403
from tests.functional.fixtures.groups import *  # noqa: F403

TEST_SETTINGS = {
    "es.url": os.environ["ELASTICSEARCH_URL"],
    "es.index": os.environ["ELASTICSEARCH_INDEX"],
    "h.app_url": "http://example.com",
    "h.authority": "example.com",
    "h.sentry_dsn_frontend": "TEST_SENTRY_DSN_FRONTEND",
    "pyramid.debug_all": False,
    "secret_key": "notasecret",
    "h_api_auth_cookie_secret_key": b"test_h_api_auth_cookie_secret_key",
    "h_api_auth_cookie_salt": b"test_h_api_auth_cookie_salt",
    "sqlalchemy.url": os.environ["DATABASE_URL"],
    "oidc_clientid_orcid": "test_oidcclientid_orcid",
    "oidc_clientsecret_orcid": "test_oidcclientid_orcid",
    "oidc_tokenurl_orcid": "test_oidc_tokenurl_orcid",
    "oidc_keyseturl_orcid": "test_oidc_keyseturl_orcid",
    "oidc_clientid_google": "test_oidcclientid_google",
    "oidc_clientsecret_google": "test_oidcclientid_google",
    "oidc_tokenurl_google": "test_oidc_tokenurl_google",
    "oidc_keyseturl_google": "test_oidc_keyseturl_google",
    "oidc_clientid_facebook": "test_oidcclientid_facebook",
    "oidc_clientsecret_facebook": "test_oidcclientid_facebook",
    "oidc_tokenurl_facebook": "test_oidc_tokenurl_facebook",
    "oidc_keyseturl_facebook": "test_oidc_keyseturl_facebook",
    "orcid_host": "https://sandbox.orcid.org",
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
    "DEV": "1",
}


@pytest.fixture(scope="session")
def app(pyramid_app):
    return TestApp(pyramid_app)


@pytest.fixture(autouse=True)
def reset_app(app):
    yield

    app.reset()


@pytest.fixture
def with_clean_db_and_search_index(db_engine, clear_search_index):
    """Empty the DB and search index before running the test.

    h doesn't normally reset the DB or search index before each functest
    because doing so was taking too long, see:
    https://github.com/hypothesis/h/pull/6845

    This does mean that functests need to be robust against data from previous
    tests still being in the DB and search index. Alternatively, a test can use
    @pytest.mark.usefixtures("with_clean_db_and_search_index") to have the DB
    and search index emptied before running the test.
    """
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

    # A test may not use the search index but may nonetheless use this
    # fixture because it wants a clean DB. In that case trying to clear the
    # search index will get a NotFoundError. Just suppress it.
    with contextlib.suppress(elasticsearch.exceptions.NotFoundError):
        clear_search_index()


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
