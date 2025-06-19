from os import environ
from unittest.mock import create_autospec

import elasticsearch_dsl
import pytest
from packaging.version import Version
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from h import search


@pytest.fixture(scope="session")
def db_engine():
    return create_engine(environ["DATABASE_URL"])


@pytest.fixture(scope="session")
def db_sessionfactory():
    return sessionmaker()


@pytest.fixture
def db_session(db_engine, db_sessionfactory):
    """
    Return the SQLAlchemy database session.

    This returns a session that is wrapped in an external transaction that is
    rolled back after each test, so tests can't make database changes that
    affect later tests.  Even if the test (or the code under test) calls
    session.commit() this won't touch the external transaction.

    Recipe adapted from:

    https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = db_sessionfactory(
        bind=connection, join_transaction_mode="create_savepoint"
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_session_replica(db_session):
    db_session.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;"))
    return db_session


@pytest.fixture
def es_client():
    client = _es_client()
    yield client
    # Push all changes to segments to make sure all annotations that were added get removed.
    elasticsearch_dsl.Index(client.index, using=client.conn).refresh()

    client.conn.delete_by_query(
        index=client.index,
        body={"query": {"match_all": {}}},
        # This query occasionally fails with a version conflict.
        # Forcing the deletion resolves the issue, but the exact
        # cause of the version conflict has not been found yet.
        conflicts="proceed",
        # Add refresh to make deletion changes show up in search results.
        refresh=True,
    )

    # Close connection to ES server to avoid ResourceWarning about a leaked TCP socket.
    client.close()


@pytest.fixture
def mock_es_client(es_client):
    return create_autospec(
        es_client,
        instance=True,
        spec_set=True,
        index="hypothesis",
        mapping_type="annotation",
        server_version=Version("6.2.0"),
    )


@pytest.fixture(scope="session")
def init_elasticsearch(request):
    """
    Initialize the elasticsearch cluster.

    Connect to the instance of Elasticsearch and initialize the index
    once per test session and delete the index after the test is completed.
    """
    es_client = _es_client()

    def maybe_delete_index():
        """Delete the test index if it exists."""
        if es_client.conn.indices.exists(index=environ["ELASTICSEARCH_INDEX"]):
            # The delete operation must be done on a concrete index, not an alias
            # in ES6. See:
            # https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-delete-index.html
            concrete_indexes = es_client.conn.indices.get(
                index=environ["ELASTICSEARCH_INDEX"]
            )
            for index in concrete_indexes:
                es_client.conn.indices.delete(index=index)

    # Delete the test search index at the end of the test run.
    request.addfinalizer(maybe_delete_index)  # noqa: PT021

    # Delete the test search index at the start of the run, just in case it
    # was somehow left behind by a previous test run.
    maybe_delete_index()

    # Initialize the test search index.
    search.init(es_client)


def _es_client():
    return search.get_client(
        {
            "es.url": environ["ELASTICSEARCH_URL"],
            "es.index": environ["ELASTICSEARCH_INDEX"],
        }
    )
