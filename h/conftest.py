# -*- coding: utf-8 -*-
"""
The `conftest` module is automatically loaded by py.test and serves as a place
to put fixture functions that are useful application-wide.
"""
import pytest

from pyramid import testing
from pyramid.paster import get_appsettings

import pyramid_basemodel
import transaction

from sqlalchemy import engine_from_config
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension

from h.api import create_db, delete_db
from h.api import store_from_settings


@pytest.fixture(scope='session', autouse=True)
def settings():
    """Default app settings (test.ini)."""
    return get_appsettings('test.ini')


@pytest.fixture(autouse=True)
def config(request, settings):
    """Pyramid configurator object."""
    req = testing.DummyRequest()
    config = testing.setUp(request=req, settings=settings)

    def destroy():
        testing.tearDown()

    request.addfinalizer(destroy)

    return config


@pytest.fixture()
def db_session(request, settings):
    """SQLAlchemy session."""
    engine = engine_from_config(settings, 'sqlalchemy.')
    pyramid_basemodel.Session = _make_session()
    pyramid_basemodel.bind_engine(engine, should_create=True, should_drop=True)

    def destroy():
        transaction.commit()
        pyramid_basemodel.Base.metadata.drop_all(engine)
        pyramid_basemodel.Session.close()

    request.addfinalizer(destroy)

    return pyramid_basemodel.Session


@pytest.fixture()
def dummy_db_session(config):
    from hem.interfaces import IDBSession

    class DummySession(object):
        def __init__(self):
            self.added = []
            self.flushed = False

        def add(self, obj):
            self.added.append(obj)

        def flush(self):
            self.flushed = True

    sess = DummySession()
    config.registry.registerUtility(sess, IDBSession)
    return sess


@pytest.fixture()
def es_connection(request, settings):
    es = store_from_settings(settings)
    create_db()
    # Pylint issue #258: https://bitbucket.org/logilab/pylint/issue/258
    #
    # pylint: disable=unexpected-keyword-arg
    es.conn.cluster.health(wait_for_status='yellow')
    request.addfinalizer(delete_db)


def _make_session():
    return scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
