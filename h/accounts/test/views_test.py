# pylint: disable=no-self-use
from collections import namedtuple

from mock import patch, Mock, MagicMock
import pytest

import deform
from pyramid import httpexceptions
from pyramid.testing import DummyRequest
from horus.interfaces import (
    IActivationClass,
    IProfileForm,
    IProfileSchema,
    IRegisterForm,
    IRegisterSchema,
    IUIStrings,
    IUserClass,
)
from horus.schemas import ProfileSchema
from horus.forms import SubmitForm
from horus.strings import UIStringsBase

from h.accounts import schemas
from h.accounts import views
from h.accounts.views import validate_form
from h.accounts.views import RegisterController
from h.accounts.views import ProfileController
from h.accounts.views import AsyncFormViewMapper
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


# A fake version of colander.Invalid for use when testing validate_form
FakeInvalid = namedtuple('FakeInvalid', 'children')


def test_validate_form_passes_data_to_validate():
    idata = {}
    form = MagicMock()

    err, data = validate_form(form, idata)

    form.validate.assert_called_with(idata)


def test_validate_form_failure():
    invalid = FakeInvalid(children=object())
    form = MagicMock()
    form.validate.side_effect = deform.ValidationFailure(None, None, invalid)

    err, data = validate_form(form, {})

    assert err == {'errors': invalid.children}
    assert data is None


def test_validate_form_ok():
    form = MagicMock()
    form.validate.return_value = {'foo': 'bar'}

    err, odata = validate_form(form, {})

    assert err is None
    assert odata == {'foo': 'bar'}


class TestProfile(object):

    """Unit tests for ProfileController's profile() method."""

    @pytest.mark.usefixtures('activation_model', 'dummy_db_session')
    def test_profile_returns_email(self, config, user_model, authn_policy):
        """profile() should include the user's email in the dict it returns."""
        request = _get_fake_request("john", "doe")
        authn_policy.authenticated_userid.return_value = "john"
        user_model.get_by_id.return_value = FakeUser(
            email="test_user@test_email.com")
        configure(config)

        profile = ProfileController(request).profile()

        assert profile["model"]["email"] == "test_user@test_email.com"


class TestEditProfile(object):

    """Unit tests for ProfileController's edit_profile() method."""

    @pytest.mark.usefixtures('activation_model', 'dummy_db_session')
    def test_profile_invalid_password(self, config, user_model):
        """Make sure our edit_profile call validates the user password."""
        request = _get_fake_request('john', 'doe')
        configure(config)

        # With an invalid password, get_user returns None
        user_model.get_user.return_value = None

        profile = ProfileController(request)
        result = profile.edit_profile()

        assert result['code'] == 401
        assert any('pwd' in err for err in result['errors'])

    @pytest.mark.usefixtures('activation_model', 'dummy_db_session')
    def test_edit_profile_with_validation_failure(self, config, user_model):
        """If validation raises edit_profile() should return an error.

        If _validate_edit_profile_request() raises an exception then
        edit_profile() should return a dict with an "errors" list containing a
        list of the error(s) from the exception's .errors property.

        """
        configure(config)
        profile = ProfileController(DummyRequest())
        errors = [
            ("email", ["That email is invalid", "That email is taken"]),
            ("emailAgain", "The emails must match."),
            ("password", ["That password is wrong"])
        ]

        with patch(
                "h.accounts.views._validate_edit_profile_request") as validate:
            validate.side_effect = (
                views._InvalidEditProfileRequestError(errors=errors))
            result = profile.edit_profile()

        assert result["errors"] == errors

    @pytest.mark.usefixtures('activation_model', 'dummy_db_session')
    def test_edit_profile_successfully(self, config, user_model):
        """edit_profile() returns a dict with key "form" when successful."""
        configure(config)
        profile = ProfileController(DummyRequest())

        with patch(
                "h.accounts.views._validate_edit_profile_request") as validate:
            validate.return_value = {
                "username": "johndoe",
                "pwd": "password",
                "subscriptions": []
            }
            result = profile.edit_profile()

        assert "form" in result
        assert "errors" not in result

    @pytest.mark.usefixtures('activation_model', 'dummy_db_session')
    def test_edit_profile_returns_email(self, config, user_model,
                                        authn_policy):
        """edit_profile()'s response should contain the user's current email.

        For a valid edit_profile() request
        horus.views.ProfileController.edit_profile() returns an HTTPRedirection
        object. h.accounts.views.ProfileController.edit_profile() should
        add a JSON body to this response containing a "model" dict with the
        user's current email address.

        AsyncFormViewMapper will pick up this JSON body and preserve it in the
        body of the 200 OK response that is finally sent back to the browser.

        The frontend uses this email field to show the user's current email
        address in the form.

        """
        configure(config)
        validate_patcher = patch(
            "h.accounts.views._validate_edit_profile_request")
        edit_profile_patcher = patch(
            "horus.views.ProfileController.edit_profile")
        get_by_id_patcher = patch("h.accounts.models.User.get_by_id")

        result = None
        try:
            validate = validate_patcher.start()
            validate.return_value = {
                "username": "fake user name",
                "pwd": "fake password",
                "subscriptions": []
            }

            edit_profile = edit_profile_patcher.start()
            edit_profile.return_value = httpexceptions.HTTPFound("fake url")

            get_by_id = get_by_id_patcher.start()
            get_by_id.return_value = FakeUser(email="fake email")

            result = ProfileController(DummyRequest()).edit_profile()

            assert result.json["model"]["email"] == "fake email"

        finally:
            validate = validate_patcher.stop()
            edit_profile = edit_profile_patcher.stop()
            get_by_id = get_by_id_patcher.stop()

    @pytest.mark.usefixtures('activation_model', 'user_model')
    def test_subscription_update(self, config, dummy_db_session):
        """Make sure that the new status is written into the DB."""
        request = _get_fake_request('acct:john@doe', 'smith', True, True)
        configure(config)

        with patch('h.accounts.views.Subscriptions') as mock_subs:
            mock_subs.get_by_id = MagicMock()
            mock_subs.get_by_id.return_value = Mock(active=True)
            profile = ProfileController(request)
            profile.edit_profile()
            assert dummy_db_session.added


class TestAsyncFormViewMapper(object):

    """Unit tests for AsyncFormViewMapper."""

    def test_it_preserves_email_in_response(self):
        """AsyncFormViewMapper should preserve the email in the response.

        ProfileController.edit_profile() returns an HTTPFound with a JSON body
        containing a model dict with the user's email address in it.

        AsyncFormViewMapper should preserve this email address in the dict
        that it returns.

        """
        mapper = AsyncFormViewMapper(attr="edit_profile")

        class ViewController(object):

            def __init__(self, request):
                pass

            def edit_profile(self):
                response = httpexceptions.HTTPFound("fake url")
                response.json = {"model": {"email": "fake email"}}
                return response

        result = mapper(ViewController)({}, DummyRequest())

        assert result["model"]["email"] == "fake email"


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
