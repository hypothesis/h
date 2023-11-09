import functools
import os
from unittest import mock

import click.testing
import deform
import pytest
import sqlalchemy
from filelock import FileLock
from pyramid import testing
from pyramid.request import apply_request_extensions
from sqlalchemy.orm import sessionmaker
from webob.multidict import MultiDict

from h import db
from h.models import Organization
from h.settings import database_url
from tests.common import factories as common_factories
from tests.common.fixtures.elasticsearch import *  # pylint:disable=wildcard-import,unused-wildcard-import
from tests.common.fixtures.services import *  # pylint:disable=wildcard-import,unused-wildcard-import

TEST_AUTHORITY = "example.com"
TEST_DATABASE_URL = database_url(
    os.environ.get("TEST_DATABASE_URL", "postgresql://postgres@localhost/htest")
)

Session = sessionmaker()


class DummyFeature:
    """
    A dummy feature flag looker-upper.

    Because we're probably testing all feature-flagged functionality, this
    feature client defaults every flag to *True*, which is the exact opposite
    of what happens outside of testing.
    """

    def __init__(self):
        self.flags = {}
        self.loaded = False

    def __call__(self, name, *args, **kwargs):
        return self.flags.get(name, True)

    def all(self):
        return self.flags


# A fake version of colander.Invalid
class FakeInvalid:
    def __init__(self, errors):
        self.errors = errors


def autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {"autospec": True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture
def cli():
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        yield runner


@pytest.fixture(scope="session")
def db_engine(tmp_path_factory):
    """Set up the database connection and create tables."""
    engine = sqlalchemy.create_engine(TEST_DATABASE_URL)

    shared_tmpdir = tmp_path_factory.getbasetemp().parent
    done_file = shared_tmpdir / "db_initialized.done"
    lock_file = shared_tmpdir / "db_initialized.lock"

    with FileLock(str(lock_file)):
        if done_file.is_file():
            pass
        else:
            db.init(
                engine, should_create=True, should_drop=True, authority=TEST_AUTHORITY
            )
            done_file.touch()

    return engine


@pytest.fixture
def default_organization(db_session):
    # This looks a bit odd, but as part of our DB initialization we always add
    # a default org. So tests can't add their own without causing a conflict.
    return (
        db_session.query(Organization).filter_by(pubid=Organization.DEFAULT_PUBID).one()
    )


@pytest.fixture
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
        if (  # pylint:disable=protected-access
            transaction.nested and not transaction._parent.nested
        ):
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


@pytest.fixture
def factories(db_session):
    common_factories.set_session(db_session)
    yield common_factories
    common_factories.set_session(None)


@pytest.fixture
def fake_feature():
    return DummyFeature()


@pytest.fixture
def form_validating_to():
    def form_validating_to(appstruct):
        form = mock.MagicMock()
        form.validate.return_value = appstruct
        form.render.return_value = "valid form"
        return form

    return form_validating_to


@pytest.fixture
def invalid_form():
    def invalid_form(errors=None):
        invalid = FakeInvalid(errors or {})
        form = mock.MagicMock()
        form.validate.side_effect = deform.ValidationFailure(None, None, invalid)
        form.render.return_value = "invalid form"
        return form

    return invalid_form


@pytest.fixture
def matchers():
    # pylint: disable=redefined-outer-name, import-outside-toplevel
    from ..common import matchers

    return matchers


@pytest.fixture
def notify(pyramid_config, request):
    patcher = mock.patch.object(pyramid_config.registry, "notify", autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def patch(request):
    return functools.partial(autopatcher, request)


@pytest.fixture
def pyramid_config(pyramid_settings, pyramid_request):
    """Return Pyramid configurator object."""
    with testing.testConfig(
        request=pyramid_request, settings=pyramid_settings
    ) as config:
        # Include pyramid_services so it's easy to set up fake services in tests
        config.include("pyramid_services")
        config.include("h.security.request_methods")
        apply_request_extensions(pyramid_request)

        yield config


@pytest.fixture
def pyramid_request(db_session, fake_feature, pyramid_settings):
    """Return pyramid request object."""
    request = testing.DummyRequest(db=db_session, feature=fake_feature)
    request.default_authority = TEST_AUTHORITY
    request.create_form = mock.Mock()
    request.matched_route = mock.Mock()
    request.registry.settings = pyramid_settings
    request.is_xhr = False
    request.params = MultiDict()
    request.GET = request.params
    request.POST = request.params
    request.user = None
    return request


@pytest.fixture
def pyramid_csrf_request(pyramid_request):
    """Return a dummy Pyramid request object with a valid CSRF token."""
    pyramid_request.headers["X-CSRF-Token"] = pyramid_request.session.get_csrf_token()
    return pyramid_request


@pytest.fixture
def pyramid_settings():
    """Return the default app settings."""
    return {"sqlalchemy.url": TEST_DATABASE_URL}
