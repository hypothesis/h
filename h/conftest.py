# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
"""
The `conftest` module is automatically loaded by py.test and serves as a place
to put fixture functions that are useful application-wide.
"""

import os

import pytest

from pyramid import testing
from pyramid.paster import get_appsettings
import transaction

from h import db
from h.api import db as api_db
from h.config import normalize_database_url


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


@pytest.fixture(scope='session', autouse=True)
def settings():
    """Default app settings (conf/test.ini)."""
    settings = get_appsettings('conf/test.ini')

    if 'TEST_DATABASE_URL' in os.environ:
        settings['sqlalchemy.url'] = normalize_database_url(
            os.environ['TEST_DATABASE_URL'])

    return settings


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
def authn_policy(config):
    from mock import MagicMock

    class DummyAuthorizationPolicy(object):
        def permits(self, *args, **kwargs):
            return True

    config.set_authorization_policy(DummyAuthorizationPolicy())
    policy = MagicMock()
    config.set_authentication_policy(policy)
    return policy


@pytest.fixture()
def db_session(request, settings):
    """SQLAlchemy session."""
    transaction.commit()
    db.Session.remove()

    engine = db.make_engine(settings)
    db.bind_engine(engine, should_create=True, should_drop=True)

    api_db.use_session(db.Session)

    return db.Session


@pytest.fixture()
def mailer(config):
    from pyramid_mailer.interfaces import IMailer
    from pyramid_mailer.testing import DummyMailer
    mailer = DummyMailer()
    config.registry.registerUtility(mailer, IMailer)
    return mailer


@pytest.fixture()
def notify(config, request):
    from mock import patch

    patcher = patch.object(config.registry, 'notify', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture()
def routes_mapper(config):
    from pyramid.interfaces import IRoutesMapper

    class DummyRoute(object):
        def __init__(self):
            self.pregenerator = None

        def generate(self, kw):
            return '/dummy/route'

    class DummyMapper(object):
        def get_route(self, route_name):
            return DummyRoute()

    mapper = DummyMapper()
    config.registry.registerUtility(mapper, IRoutesMapper)
    return mapper


def _make_session():
    return scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
