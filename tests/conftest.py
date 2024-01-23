import pytest
from sqlalchemy import event


@pytest.fixture
def db_session(db_engine, db_sessionfactory):
    """
    Return the SQLAlchemy database session.

    h overrides the db_session fixture from h-testkit because h still uses
    SQLAlchemy 1.4 so it has to use the older, 1.4 version of the SQLAlchemy
    test suite technique:

    https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites

    When h is upgraded to SQLAlchemy 2 this fixture can be removed and it can
    just use the one from h-testkit.
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
