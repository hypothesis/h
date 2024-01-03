from os import environ

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


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

    This is the same technique as used in SQLAlchemy's own CI.
    Since h still uses SQLAlchemy 1.4 it uses the older, 1.4 version of the
    technique:

    https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites

    When h is upgraded to SQLAlchemy 2 we can upgrade this fixture to use the
    newer, SQLAlchemy 2 version of the technique:
    https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = db_sessionfactory(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if (  # pylint:disable=protected-access
            transaction.nested and not transaction._parent.nested
        ):
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
