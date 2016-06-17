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

from pyramid import testing
from pyramid.request import apply_request_extensions

from h import db
from h import form
from h.api import db as api_db
from h.settings import database_url


TEST_DATABASE_URL = database_url(os.environ.get('TEST_DATABASE_URL',
                                                'postgresql://postgres@localhost/htest'))

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


@pytest.fixture(scope='session', autouse=True)
def setup_database():
    """Set up the database connection and create tables."""
    engine = db.make_engine({'sqlalchemy.url': TEST_DATABASE_URL})
    db.bind_engine(engine, should_create=True, should_drop=True)
    api_db.use_session(db.Session)


@pytest.fixture(autouse=True)
def db_session(request, monkeypatch):
    """
    Prepare the SQLAlchemy session object.

    We enable fast repeatable database tests by setting up the database only
    once per session (see :func:`setup_database`) and then wrapping each test
    function in a SAVEPOINT/ROLLBACK TO SAVEPOINT within the transaction.
    """
    db.Session.begin_nested()
    request.addfinalizer(db.Session.rollback)

    # Prevent the session from committing, but simulate the effects of a commit
    # within our transaction. N.B. we must not only flush SQLA state to the
    # database but also expire the persistence state of all objects.
    def _fake_commit():
        db.Session.flush()
        db.Session.expire_all()
    monkeypatch.setattr(db.Session, 'commit', _fake_commit)
    # Prevent the session from closing (make it a no-op):
    monkeypatch.setattr(db.Session, 'remove', lambda: None)

    return db.Session()


@pytest.fixture(scope='session', autouse=True)
def deform():
    """Allow tests that use deform to find our custom templates."""
    form.init()


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
