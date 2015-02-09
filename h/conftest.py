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


def _make_session():
    return scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
