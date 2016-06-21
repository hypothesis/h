# -*- coding: utf-8 -*-

import os

import pytest
from sqlalchemy import engine_from_config
from sqlalchemy.orm import scoped_session, sessionmaker

from h.api import db

Session = scoped_session(sessionmaker())


@pytest.fixture
def config(request, settings):
    """Pyramid configurator object."""
    from pyramid import testing
    config = testing.setUp(settings=settings)
    request.addfinalizer(testing.tearDown)
    return config


@pytest.fixture(scope='session')
def settings():
    """Default app settings."""
    settings = {}
    settings['sqlalchemy.url'] = os.environ.get('TEST_DATABASE_URL',
                                                'postgresql://postgres@localhost/htest')
    return settings


@pytest.fixture(autouse=True)
def db_session(request, monkeypatch):
    """
    Prepare the SQLAlchemy session object.

    We enable fast repeatable database tests by setting up the database only
    once per session (see :func:`setup_database`) and then wrapping each test
    function in a SAVEPOINT/ROLLBACK TO SAVEPOINT within the transaction.
    """
    Session.begin_nested()
    request.addfinalizer(Session.rollback)

    # Prevent the session from committing, but simulate the effects of a commit
    # within our transaction. N.B. we must not only flush SQLA state to the
    # database but also expire the persistence state of all objects.
    def _fake_commit():
        Session.flush()
        Session.expire_all()
    monkeypatch.setattr(Session, 'commit', _fake_commit)
    # Prevent the session from closing (make it a no-op):
    monkeypatch.setattr(Session, 'remove', lambda: None)
    return Session


@pytest.fixture(scope='module', autouse=True)
def setup_database(request, settings):
    """Set up the database connection and create tables."""
    engine = engine_from_config(settings, 'sqlalchemy.')
    db.bind_engine(engine, should_create=True, should_drop=True)
    request.addfinalizer(Session.remove)
