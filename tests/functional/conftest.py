import contextlib
import os
from multiprocessing import Process
from time import sleep

import pytest
import requests
from pyramid.scripts import pserve
from webtest import TestApp

from h import db
from h.app import create_app
from tests.common import factories as factories_common
from tests.common.fixtures import es_client  # pylint:disable=unused-import
from tests.common.fixtures import init_elasticsearch  # pylint:disable=unused-import
from tests.common.fixtures.elasticsearch import ELASTICSEARCH_INDEX, ELASTICSEARCH_URL
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
    "sqlalchemy.url": os.environ.get(
        "TEST_DATABASE_URL", "postgresql://postgres@localhost/htest"
    ),
}


@pytest.fixture(scope="session")
def app(pyramid_app):
    return TestApp(pyramid_app)


@pytest.fixture(scope="class")
def ws_app():
    # In order to run the websocket separately, set this to True and run the
    # websocket with DATABASE_URL=postgresql://postgres@localhost/htest
    EXTERNAL_WS = False

    if EXTERNAL_WS:
        yield TestApp("http://localhost:5001")
        return

    def serve():
        os.environ["DATABASE_URL"] = TEST_SETTINGS["sqlalchemy.url"]
        # First arg here is the script filename. The value is irrelevant
        pserve.main(argv=["pserve", "conf/websocket-dev.ini"])

    proc = Process(target=serve)
    proc.start()

    def health_check():
        try:
            return requests.get("http://localhost:5001").json()
        except Exception:  # pylint: disable=broad-except
            pass

        return False

    for _retry in range(6):
        if health_check():
            break

        print("Waiting for WS to start...")
        sleep(0.5)

    if not health_check():
        raise EnvironmentError("Could not start WS")

    yield TestApp("http://localhost:5001")

    proc.kill()
    proc.join()


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
        conn.execute("TRUNCATE {};".format(tnames))
        tx.commit()

    # We need to re-init the DB as it creates the default test group and
    # possibly more in future?
    db.init(db_engine, authority=TEST_SETTINGS["h.authority"])


@pytest.fixture(scope="session")
def db_engine():
    db_engine = db.make_engine(TEST_SETTINGS)
    db.init(db_engine, authority=TEST_SETTINGS["h.authority"], should_create=True)

    yield db_engine

    db_engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Get a standalone database session for preparing database state."""
    session = db.Session(bind=db_engine)
    yield session
    session.close()


@pytest.fixture
def factories(db_session):
    factories_common.set_session(db_session)
    yield factories_common
    factories_common.set_session(None)


@pytest.fixture(scope="session", autouse=True)
def init_db(db_engine):

    authority = TEST_SETTINGS["h.authority"]
    db.init(db_engine, should_drop=True, should_create=True, authority=authority)


@pytest.fixture(scope="session")
def pyramid_app():
    return create_app(None, **TEST_SETTINGS)


# Always unconditionally wipe the Elasticsearch index after every functional
# test.
@pytest.fixture(autouse=True)
def always_delete_all_elasticsearch_documents():
    pass
