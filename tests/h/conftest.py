# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
"""
The `conftest` module is automatically loaded by py.test and serves as a place
to put fixture functions that are useful application-wide.
"""

import functools
import os

import mock
import pytest

import sqlalchemy
from pyramid import testing
from pyramid.request import apply_request_extensions
from sqlalchemy.orm import sessionmaker

from h import db
from h import form
from h.settings import database_url

TEST_DATABASE_URL = database_url(os.environ.get('TEST_DATABASE_URL',
                                                'postgresql://postgres@localhost/htest'))

Session = sessionmaker()


class DummyFeature(object):

    """
    A dummy feature flag looker-upper.

    Because we're probably testing all feature-flagged functionality, this
    feature client defaults every flag to *True*, which is the exact opposite
    of what happens outside of testing.
    """

    def __init__(self):
        self.flags = {}

    def __call__(self, name, *args, **kwargs):
        return self.flags.get(name, True)


class DummySession(object):

    """
    A dummy database session.
    """

    def __init__(self):
        self.added = []
        self.deleted = []
        self.flushed = False

    def add(self, obj):
        self.added.append(obj)

    def delete(self, obj):
        self.deleted.append(obj)

    def flush(self):
        self.flushed = True


def autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {'autospec': True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture(scope='session')
def db_engine():
    """Set up the database connection and create tables."""
    engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
    db.init(engine, should_create=True, should_drop=True)
    return engine


@pytest.yield_fixture
def db_session(db_engine):
    """
    Prepare the SQLAlchemy session object.

    We enable fast repeatable database tests by setting up the database only
    once per session (see :func:`db_engine`) and then wrapping each test
    function in a transaction that is rolled back.

    Additionally, we set a SAVEPOINT before entering the test, and if we
    detect that the test has committed (i.e. released the savepoint) we
    immediately open another. This has the effect of preventing test code from
    committing the outer transaction.
    """
    conn = db_engine.connect()
    trans = conn.begin()
    session = Session(bind=conn)
    session.begin_nested()

    @sqlalchemy.event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


@pytest.fixture(scope='session', autouse=True)
def deform():
    """Use our custom Deform renderer instead of Deform's default one."""
    form.initialize_deform_renderer(config=mock.Mock())


@pytest.yield_fixture
def factories(db_session):
    from ..common import factories
    factories.SESSION = db_session
    yield factories
    factories.SESSION = None


@pytest.fixture
def fake_feature():
    return DummyFeature()


@pytest.fixture
def fake_db_session():
    return DummySession()


@pytest.fixture
def mailer(pyramid_config):
    from pyramid_mailer.interfaces import IMailer
    from pyramid_mailer.testing import DummyMailer
    mailer = DummyMailer()
    pyramid_config.registry.registerUtility(mailer, IMailer)
    return mailer


@pytest.fixture
def matchers():
    from ..common import matchers
    return matchers


@pytest.fixture
def notify(pyramid_config, request):
    patcher = mock.patch.object(pyramid_config.registry, 'notify', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def patch(request):
    return functools.partial(autopatcher, request)


@pytest.yield_fixture
def pyramid_config(pyramid_settings, pyramid_request):
    """Pyramid configurator object."""
    with testing.testConfig(request=pyramid_request,
                            settings=pyramid_settings) as config:
        # Include pyramid_services so it's easy to set up fake services in tests
        config.include('pyramid_services')
        apply_request_extensions(pyramid_request)

        yield config


@pytest.fixture
def pyramid_request(db_session, fake_feature, pyramid_settings):
    """Dummy Pyramid request object."""
    request = testing.DummyRequest(db=db_session, feature=fake_feature)
    request.auth_domain = request.domain
    request.registry.settings = pyramid_settings
    return request


@pytest.fixture
def pyramid_csrf_request(pyramid_request):
    """Dummy Pyramid request object with a valid CSRF token."""
    pyramid_request.headers['X-CSRF-Token'] = pyramid_request.session.get_csrf_token()
    return pyramid_request


@pytest.fixture
def pyramid_settings():
    """Default app settings."""
    return {
        'sqlalchemy.url': TEST_DATABASE_URL
    }
