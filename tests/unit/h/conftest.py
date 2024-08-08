import functools
import os
from unittest import mock

import click.testing
import deform
import pytest
from pyramid import testing
from pyramid.request import apply_request_extensions
from webob.multidict import MultiDict

from h.models import Organization
from h.models.auth_client import GrantType
from h.security import Identity
from tests.common import factories as common_factories
from tests.common.fixtures.elasticsearch import *  # pylint:disable=wildcard-import,unused-wildcard-import
from tests.common.fixtures.services import *  # pylint:disable=wildcard-import,unused-wildcard-import


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


@pytest.fixture
def default_organization(db_session):
    # This looks a bit odd, but as part of our DB initialization we always add
    # a default org. So tests can't add their own without causing a conflict.
    return (
        db_session.query(Organization).filter_by(pubid=Organization.DEFAULT_PUBID).one()
    )


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
    from tests.common import matchers

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
def pyramid_request(db_session, db_session_replica, fake_feature, pyramid_settings):
    """Return pyramid request object."""
    request = testing.DummyRequest(
        db=db_session, db_replica=db_session_replica, feature=fake_feature
    )
    request.default_authority = "example.com"
    request.create_form = mock.Mock()

    request.matched_route = mock.Mock(spec=["name"])
    # `name` is a special argument to the Mock constructor so if you want a
    # mock to have a `name` attribute you can't just do Mock(name="name"), you
    # have to use a separate call to configure_mock() instead.
    # https://docs.python.org/3/library/unittest.mock.html#mock-names-and-the-name-attribute
    request.matched_route.configure_mock(name="index")

    request.registry.settings = pyramid_settings
    request.is_xhr = False
    request.params = MultiDict()
    request.GET = request.params
    request.POST = request.params
    request.user = None
    request.scheme = "https"
    return request


@pytest.fixture
def pyramid_csrf_request(pyramid_request):
    """Return a dummy Pyramid request object with a valid CSRF token."""
    pyramid_request.headers["X-CSRF-Token"] = pyramid_request.session.get_csrf_token()
    pyramid_request.referrer = "https://example.com"
    pyramid_request.host_port = "80"
    return pyramid_request


@pytest.fixture
def pyramid_settings():
    """Return the default app settings."""
    return {"sqlalchemy.url": os.environ["DATABASE_URL"]}


@pytest.fixture
def auth_client(factories):
    return factories.ConfidentialAuthClient(grant_type=GrantType.client_credentials)


@pytest.fixture
def with_auth_client(auth_client, pyramid_config):
    pyramid_config.testing_securitypolicy(
        identity=Identity.from_models(auth_client=auth_client)
    )
