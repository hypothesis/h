# pylint: disable=no-self-use
from mock import patch, Mock, MagicMock
import pytest

from pyramid.testing import DummyRequest
from horus.interfaces import (
    IUserClass, IActivationClass, IUIStrings, IProfileSchema, IProfileForm,
    IRegisterSchema, IRegisterForm
)
from horus.schemas import ProfileSchema
from horus.forms import SubmitForm
from horus.strings import UIStringsBase

from h.accounts.views import RegisterController
from h.accounts.views import ProfileController
from h.models import _


class FakeUser(object):
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])


class FakeDB(object):
    def add(self):
        return True


def configure(config):
    config.registry.registerUtility(UIStringsBase, IUIStrings)
    config.registry.registerUtility(ProfileSchema, IProfileSchema)
    config.registry.registerUtility(SubmitForm, IProfileForm)
    config.registry.registerUtility(MagicMock(), IRegisterSchema)
    config.registry.registerUtility(MagicMock(), IRegisterForm)
    config.registry.feature = MagicMock()
    config.registry.feature.return_value = None


def _mock_db_session_query_method():
    """Return a mock session.query() that passes unique_email validation.

    Return a callable that returns an object with a filter() method that
    returns an object with a first() method that returns None.

    When attached to a dummy_db_session object as dummy_db_session.query()
    this callable will cause Horus's unique_email validation check to pass.

    """
    result = MagicMock()
    result.first.return_value = None
    filter_ = MagicMock()
    filter_.filter.return_value = result
    def query(*args, **kwargs):
        return filter_
    return query


def _get_fake_request(username, password, with_subscriptions=False, active=True):
    fake_request = DummyRequest()

    def get_fake_token():
        return 'fake_token'

    fake_request.params['csrf_token'] = 'fake_token'
    fake_request.session.get_csrf_token = get_fake_token
    fake_request.POST['username'] = username
    fake_request.POST['pwd'] = password

    if with_subscriptions:
        subs = '{"active": activestate, "uri": "username", "id": 1}'
        subs = subs.replace('activestate', str(active).lower()).replace('username', username)
        fake_request.POST['subscriptions'] = subs
    return fake_request


@pytest.mark.usefixtures('activation_model', 'dummy_db_session')
def test_profile_returns_email(config, user_model, authn_policy):
    """profile() should include the user's email in the dict it returns."""
    request = _get_fake_request("john", "doe")
    authn_policy.authenticated_userid.return_value = "john"
    user_model.get_by_id.return_value = FakeUser(
        email="test_user@test_email.com")
    configure(config)

    profile = ProfileController(request).profile()

    assert profile["model"]["email"] == "test_user@test_email.com"


@pytest.mark.usefixtures('activation_model',
                         'dummy_db_session')
def test_profile_invalid_password(config, user_model):
    """Make sure our edit_profile call validates the user password"""
    request = _get_fake_request('john', 'doe')
    configure(config)

    # With an invalid password, get_user returns None
    user_model.get_user.return_value = None

    profile = ProfileController(request)
    result = profile.edit_profile()

    assert result['code'] == 401
    assert any('pwd' in err for err in result['errors'])


@pytest.mark.usefixtures('activation_model',
                         'dummy_db_session')
def test_edit_profile_with_non_matching_emails(
        config, user_model, dummy_db_session):
    """edit_profile() should return an error if the emails don't match."""
    request = _get_fake_request('john', 'doe')
    request.params["email"] = "example@example.com"
    request.params["emailAgain"] = "different@example.com"
    configure(config)

    dummy_db_session.query = _mock_db_session_query_method()

    profile = ProfileController(request)
    result = profile.edit_profile()

    assert "errors" in result
    assert result["errors"][0][1] == "The emails must match."


@pytest.mark.usefixtures('activation_model',
                         'dummy_db_session')
def test_edit_profile_with_invalid_email(config, user_model, dummy_db_session):
    """edit_profile() should return an error if the new email is invalid."""
    request = _get_fake_request('john', 'doe')
    request.params["email"] = "foo@bar"
    request.params["emailAgain"] = "foo@bar"
    configure(config)

    dummy_db_session.query = _mock_db_session_query_method()

    profile = ProfileController(request)
    result = profile.edit_profile()

    assert result["errors"][0][1][0] == "Invalid email address"


@pytest.mark.usefixtures('activation_model',
                         'dummy_db_session')
def test_edit_profile_with_taken_email(config, user_model, dummy_db_session):
    """edit_profile() should return an error if the email is already taken."""
    request = _get_fake_request('john', 'doe')
    request.params["email"] = "john@doe.com"
    request.params["emailAgain"] = "john@doe.com"
    configure(config)

    # Mock dummy_db_session.query() so that Horus's unique_email validation
    # check will fail.
    first = MagicMock()
    first.email = "john@doe.com"
    results = MagicMock()
    results.first.return_value = first
    filter_ = MagicMock()
    filter_.filter.return_value = results
    def query(*args, **kwargs):
        return filter_
    dummy_db_session.query = query

    profile = ProfileController(request)
    result = profile.edit_profile()

    assert "errors" in result
    assert result["errors"][0][1][0] == (
        "Sorry, an account with the email john@doe.com already exists. Try "
        "logging in instead.")


@pytest.mark.usefixtures('activation_model',
                         'dummy_db_session')
def test_edit_profile_successfully(config, user_model, dummy_db_session):
    """edit_profile() returns a dict with key "form" when successful."""
    request = _get_fake_request('john', 'doe')
    request.params["email"] = "example@example.com"
    request.params["emailAgain"] = "example@example.com"
    configure(config)

    dummy_db_session.query = _mock_db_session_query_method()

    profile = ProfileController(request)
    result = profile.edit_profile()

    assert "form" in result
    assert "errors" not in result

@pytest.mark.usefixtures('activation_model',
                         'user_model')
def test_subscription_update(config, dummy_db_session):
    """
    Make sure that the new status is written into the DB
    """
    request = _get_fake_request('acct:john@doe', 'smith', True, True)
    configure(config)

    with patch('h.accounts.views.Subscriptions') as mock_subs:
        mock_subs.get_by_id = MagicMock()
        mock_subs.get_by_id.return_value = Mock(active=True)
        profile = ProfileController(request)
        profile.edit_profile()
        assert dummy_db_session.added


@pytest.mark.usefixtures('activation_model',
                         'dummy_db_session')
def test_disable_invalid_password(config, user_model):
    """
    Make sure our disable_user call validates the user password
    """
    request = _get_fake_request('john', 'doe')
    configure(config)

    # With an invalid password, get_user returns None
    user_model.get_user.return_value = None

    profile = ProfileController(request)
    result = profile.disable_user()

    assert result['code'] == 401
    assert any('pwd' in err for err in result['errors'])


@pytest.mark.usefixtures('activation_model',
                         'dummy_db_session')
def test_user_disabled(config, user_model):
    """
    Check if the user is disabled
    """
    request = _get_fake_request('john', 'doe')
    configure(config)

    user = FakeUser(password='abc')
    user_model.get_user.return_value = user

    profile = ProfileController(request)
    profile.disable_user()

    assert user.password == user_model.generate_random_password.return_value


@pytest.mark.usefixtures('activation_model',
                         'dummy_db_session',
                         'mailer',
                         'routes_mapper',
                         'user_model')
def test_registration_does_not_autologin(config, authn_policy):
    configure(config)

    request = DummyRequest()
    request.method = 'POST'
    request.POST.update({'email': 'giraffe@example.com',
                         'password': 'secret',
                         'username': 'giraffe'})

    ctrl = RegisterController(request)
    ctrl.register()

    assert not authn_policy.remember.called


@pytest.fixture
def user_model(config):
    mock = MagicMock()
    config.registry.registerUtility(mock, IUserClass)
    return mock


@pytest.fixture
def activation_model(config):
    mock = MagicMock()
    config.registry.registerUtility(mock, IActivationClass)
    return mock
