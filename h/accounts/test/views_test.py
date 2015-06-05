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

from h.accounts.views import ajax_form
from h.accounts.views import validate_form
from h.accounts.views import AuthController
from h.accounts.views import ForgotPasswordController
from h.accounts.views import RegisterController
from h.accounts.views import ProfileController


class FakeUser(object):
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])


def configure(config):
    config.registry.registerUtility(UIStringsBase, IUIStrings)
    config.registry.registerUtility(ProfileSchema, IProfileSchema)
    config.registry.registerUtility(SubmitForm, IProfileForm)
    config.registry.registerUtility(MagicMock(), IRegisterSchema)
    config.registry.registerUtility(MagicMock(), IRegisterForm)
    config.registry.feature = MagicMock()
    config.registry.feature.return_value = None


# A fake version of colander.Invalid for use when testing validate_form
FakeInvalid = namedtuple('FakeInvalid', 'children')


def test_ajax_form_handles_http_redirect_as_success():
    request = DummyRequest()
    result = ajax_form(request, httpexceptions.HTTPFound())

    assert result['status'] == 'okay'
    assert request.response.status_code == 200


def test_ajax_form_handles_http_error_as_error():
    request = DummyRequest()
    result = ajax_form(request, httpexceptions.HTTPInsufficientStorage())

    assert result['status'] == 'failure'
    assert result['reason'] == \
        'There was not enough space to save the resource'
    assert request.response.status_code == 507


def test_ajax_form_sets_failure_status_on_errors():
    request = DummyRequest()
    result = ajax_form(request, {'errors': 'data'})

    assert result['status'] == 'failure'


def test_ajax_form_sets_status_code_400_on_errors():
    request = DummyRequest()
    _ = ajax_form(request, {'errors': 'data'})

    assert request.response.status_code == 400


def test_ajax_form_sets_status_code_from_input_on_errors():
    request = DummyRequest()
    _ = ajax_form(request, {'errors': 'data', 'code': 418})

    assert request.response.status_code == 418


def test_ajax_form_aggregates_errors_on_success():
    request = DummyRequest()
    errors = [
        {'name': 'Name is too weird'},
        {'email': 'Email must be @hotmail.com'},
    ]
    result = ajax_form(request, {'errors': errors})

    assert result['errors'] == {'name': 'Name is too weird',
                                'email': 'Email must be @hotmail.com'}


def test_ajax_form_passes_data_through_on_success():
    request = DummyRequest()
    result = ajax_form(request, {'some': 'data', 'no': 'errors'})

    assert result['some'] == 'data'
    assert result['no'] == 'errors'
    assert request.response.status_code == 200


def test_ajax_form_ignores_status_code_from_input_on_success():
    request = DummyRequest()
    result = ajax_form(request, {'some': 'data', 'code': 418})

    assert request.response.status_code == 200


def test_ajax_form_includes_flash_data(pop_flash):
    request = DummyRequest()
    pop_flash.return_value = {'success': ['Well done!']}
    result = ajax_form(request, {'some': 'data'})

    assert result['flash'] == {'success': ['Well done!']}


def test_ajax_form_sets_status_code_400_on_flash_error(pop_flash):
    request = DummyRequest()
    pop_flash.return_value = {'error': ['I asplode!']}
    _ = ajax_form(request, {'some': 'data'})

    assert request.response.status_code == 400


def test_ajax_form_sets_status_failure_on_flash_error(pop_flash):
    request = DummyRequest()
    pop_flash.return_value = {'error': ['I asplode!']}
    result = ajax_form(request, {'some': 'data'})

    assert result['status'] == 'failure'


def test_ajax_form_sets_reason_on_flash_error(pop_flash):
    request = DummyRequest()
    pop_flash.return_value = {'error': ['I asplode!']}
    result = ajax_form(request, {'some': 'data'})

    assert result['reason'] == 'I asplode!'


def test_validate_form_passes_data_to_validate():
    form = MagicMock()

    _, _ = validate_form(form, {})

    form.validate.assert_called_with({})


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

    err, data = validate_form(form, {})

    assert err is None
    assert data == {'foo': 'bar'}


@pytest.mark.usefixtures('routes_mapper')
def test_login_redirects_when_logged_in(authn_policy):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

    result = AuthController(request).login()

    assert isinstance(result, httpexceptions.HTTPFound)


@pytest.mark.usefixtures('routes_mapper')
def test_login_returns_error_when_validation_fails(authn_policy,
                                                   form_validator):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = None  # Logged out
    form_validator.return_value = ({"errors": "KABOOM!"}, None)

    result = AuthController(request).login()

    assert result == {"errors": "KABOOM!"}


@pytest.mark.usefixtures('routes_mapper')
@patch('h.accounts.views.LoginEvent', autospec=True)
def test_login_no_event_when_validation_fails(loginevent,
                                              authn_policy,
                                              form_validator,
                                              notify):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = None  # Logged out
    form_validator.return_value = ({"errors": "KABOOM!"}, None)

    AuthController(request).login()

    assert not loginevent.called
    assert not notify.called



@pytest.mark.usefixtures('routes_mapper')
def test_login_returns_success_when_validation_succeeds(authn_policy,
                                                        form_validator):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = None  # Logged out
    form_validator.return_value = (None, {"user": FakeUser()})

    result = AuthController(request).login()

    assert result == {}


@pytest.mark.usefixtures('routes_mapper')
@patch('h.accounts.views.LoginEvent', autospec=True)
def test_login_event_when_validation_succeeds(loginevent,
                                              authn_policy,
                                              form_validator,
                                              notify):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = None  # Logged out
    elephant = FakeUser()
    form_validator.return_value = (None, {"user": elephant})

    AuthController(request).login()

    loginevent.assert_called_with(request, elephant)
    notify.assert_called_with(loginevent.return_value)


@pytest.mark.usefixtures('routes_mapper')
@patch('h.accounts.views.LogoutEvent', autospec=True)
def test_logout_event(logoutevent, notify):
    request = DummyRequest()

    result = AuthController(request).logout()

    logoutevent.assert_called_with(request)
    notify.assert_called_with(logoutevent.return_value)


@pytest.mark.usefixtures('routes_mapper')
def test_logout_invalidates_session():
    request = DummyRequest()
    request.session["foo"] = "bar"

    result = AuthController(request).logout()

    assert "foo" not in request.session


@pytest.mark.usefixtures('routes_mapper')
def test_logout_redirects():
    request = DummyRequest()

    result = AuthController(request).logout()

    assert isinstance(result, httpexceptions.HTTPFound)


@pytest.mark.usefixtures('routes_mapper')
def test_logout_forgets_authenticated_user(authn_policy):
    request = DummyRequest()

    AuthController(request).logout()

    authn_policy.forget.assert_called_with(request)


@pytest.mark.usefixtures('routes_mapper')
def test_logout_response_has_forget_headers(authn_policy):
    request = DummyRequest()
    authn_policy.forget.return_value = {'x-erase-fingerprints': 'on the hob'}

    result = AuthController(request).logout()

    assert result.headers['x-erase-fingerprints'] == 'on the hob'


forgot_password_fixtures = pytest.mark.usefixtures('activation_model',
                                                   'authn_policy',
                                                   'dummy_db_session',
                                                   'form_validator',
                                                   'mailer',
                                                   'routes_mapper',
                                                   'user_model')


@forgot_password_fixtures
def test_forgot_password_returns_error_when_validation_fails(authn_policy,
                                                             form_validator):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    form_validator.return_value = ({"errors": "KABOOM!"}, None)

    result = ForgotPasswordController(request).forgot_password()

    assert result == {"errors": "KABOOM!"}


@forgot_password_fixtures
def test_forgot_password_fetches_user_by_form_email(authn_policy,
                                                    form_validator,
                                                    user_model):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    form_validator.return_value = (None, {"email": "giraffe@thezoo.org"})

    ForgotPasswordController(request).forgot_password()

    user_model.get_by_email.assert_called_with(request, "giraffe@thezoo.org")


@forgot_password_fixtures
def test_forgot_password_creates_activation_for_user(activation_model,
                                                     authn_policy,
                                                     dummy_db_session,
                                                     form_validator,
                                                     user_model):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    form_validator.return_value = (None, {"email": "giraffe@thezoo.org"})

    ForgotPasswordController(request).forgot_password()


    user = user_model.get_by_email.return_value
    activation = activation_model.return_value

    activation_model.assert_called_with()
    assert activation in dummy_db_session.added
    assert user.activation == activation


@patch('h.accounts.views.reset_password_link')
@forgot_password_fixtures
def test_forgot_password_generates_reset_link_from_activation(reset_link,
                                                              activation_model,
                                                              authn_policy,
                                                              form_validator):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    form_validator.return_value = (None, {"email": "giraffe@thezoo.org"})
    activation_model.return_value.code = "abcde12345"

    ForgotPasswordController(request).forgot_password()

    reset_link.assert_called_with(request, "abcde12345")


@patch('h.accounts.views.reset_password_email')
@patch('h.accounts.views.reset_password_link')
@forgot_password_fixtures
def test_forgot_password_generates_mail(reset_link,
                                        reset_mail,
                                        activation_model,
                                        authn_policy,
                                        form_validator,
                                        user_model):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    form_validator.return_value = (None, {"email": "giraffe@thezoo.org"})
    activation_model.return_value.code = "abcde12345"
    reset_link.return_value = "http://example.com"
    giraffe = FakeUser()
    user_model.get_by_email.return_value = giraffe

    ForgotPasswordController(request).forgot_password()

    reset_mail.assert_called_with(giraffe, "abcde12345", "http://example.com")


@patch('h.accounts.views.reset_password_email')
@forgot_password_fixtures
def test_forgot_password_sends_mail(reset_mail,
                                    authn_policy,
                                    mailer,
                                    form_validator):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    form_validator.return_value = (None, {"email": "giraffe@thezoo.org"})
    message = reset_mail.return_value

    ForgotPasswordController(request).forgot_password()

    assert message in mailer.outbox


@forgot_password_fixtures
def test_forgot_password_redirects_on_success(authn_policy,
                                              form_validator):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    form_validator.return_value = (None, {"email": "giraffe@thezoo.org"})

    result = ForgotPasswordController(request).forgot_password()

    assert isinstance(result, httpexceptions.HTTPRedirection)


@pytest.mark.usefixtures('routes_mapper')
def test_forgot_password_form_redirects_when_logged_in(authn_policy):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

    result = ForgotPasswordController(request).forgot_password_form()

    assert isinstance(result, httpexceptions.HTTPFound)


reset_password_fixtures = pytest.mark.usefixtures('activation_model',
                                                  'dummy_db_session',
                                                  'notify',
                                                  'routes_mapper',
                                                  'user_model')


@reset_password_fixtures
def test_reset_password_not_found_if_code_missing():
    request = DummyRequest(method='POST')

    result = ForgotPasswordController(request).reset_password()

    assert isinstance(result, httpexceptions.HTTPNotFound)


@reset_password_fixtures
def test_reset_password_looks_up_code_in_database(activation_model):
    request = DummyRequest(method='POST', matchdict={'code': 'abc123'})
    activation_model.get_by_code.return_value = None

    result = ForgotPasswordController(request).reset_password()

    activation_model.get_by_code.assert_called_with(request, 'abc123')


@reset_password_fixtures
def test_reset_password_not_found_if_code_not_found(activation_model):
    request = DummyRequest(method='POST', matchdict={'code': 'abc123'})
    activation_model.get_by_code.return_value = None

    result = ForgotPasswordController(request).reset_password()

    assert isinstance(result, httpexceptions.HTTPNotFound)


@reset_password_fixtures
def test_reset_password_looks_up_user_by_activation(activation_model,
                                                    user_model):
    request = DummyRequest(method='POST', matchdict={'code': 'abc123'})
    activation = activation_model.get_by_code.return_value
    user_model.get_by_activation.return_value = None

    result = ForgotPasswordController(request).reset_password()

    user_model.get_by_activation.assert_called_with(request, activation)


@reset_password_fixtures
def test_reset_password_not_found_if_user_not_found(user_model):
    request = DummyRequest(method='POST', matchdict={'code': 'abc123'})
    user_model.get_by_activation.return_value = None

    result = ForgotPasswordController(request).reset_password()

    assert isinstance(result, httpexceptions.HTTPNotFound)


@reset_password_fixtures
def test_reset_password_forbids_GET():
    request = DummyRequest(matchdict={'code': 'abc123'})

    result = ForgotPasswordController(request).reset_password()

    assert isinstance(result, httpexceptions.HTTPMethodNotAllowed)


@reset_password_fixtures
def test_reset_password_returns_error_on_error(form_validator):
    request = DummyRequest(method='POST', matchdict={'code': 'abc123'})
    form_validator.return_value = ({"errors": "KABOOM!"}, None)

    result = ForgotPasswordController(request).reset_password()

    assert result == {"errors": "KABOOM!"}


@reset_password_fixtures
def test_reset_password_sets_user_password_from_form(form_validator,
                                                     user_model):
    request = DummyRequest(method='POST', matchdict={'code': 'abc123'})
    form_validator.return_value = (None, {"password": "s3cure!"})
    elephant = FakeUser(password='password1')
    user_model.get_by_activation.return_value = elephant

    ForgotPasswordController(request).reset_password()

    assert elephant.password == 's3cure!'


@reset_password_fixtures
def test_reset_password_deletes_activation(activation_model,
                                           dummy_db_session,
                                           form_validator):
    request = DummyRequest(method='POST', matchdict={'code': 'abc123'})
    form_validator.return_value = (None, {"password": "s3cure!"})
    activation = activation_model.get_by_code.return_value

    ForgotPasswordController(request).reset_password()

    assert activation in dummy_db_session.deleted


@patch('h.accounts.views.PasswordResetEvent', autospec=True)
@reset_password_fixtures
def test_reset_password_emits_event(event, form_validator, notify, user_model):
    request = DummyRequest(method='POST', matchdict={'code': 'abc123'})
    form_validator.return_value = (None, {"password": "s3cure!"})
    elephant = FakeUser(password='password1')
    user_model.get_by_activation.return_value = elephant

    ForgotPasswordController(request).reset_password()

    event.assert_called_with(request, elephant)
    notify.assert_called_with(event.return_value)


@reset_password_fixtures
def test_reset_password_redirects_on_success(form_validator):
    request = DummyRequest(method='POST', matchdict={'code': 'abc123'})
    form_validator.return_value = (None, {"password": "s3cure!"})

    result = ForgotPasswordController(request).reset_password()

    assert isinstance(result, httpexceptions.HTTPRedirection)


@pytest.mark.usefixtures('subscriptions_model')
def test_profile_looks_up_by_logged_in_user(authn_policy, user_model):
    """
    When fetching the profile, look up email for the logged in user.

    (And don't, for example, use a 'username' passed to us in params.)
    """
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:foo@bar.com"

    ProfileController(request).profile()

    user_model.get_by_id.assert_called_with(request, "acct:foo@bar.com")


@pytest.mark.usefixtures('user_model')
def test_profile_looks_up_subs_by_logged_in_user(authn_policy,
                                                 subscriptions_model):
    """
    When fetching the profile, look up subscriptions for the logged in user.

    (And don't, for example, use a 'username' passed to us in params.)
    """
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:foo@bar.com"

    ProfileController(request).profile()

    subscriptions_model.get_subscriptions_for_uri.assert_called_with(
        request, "acct:foo@bar.com")


@pytest.mark.usefixtures('subscriptions_model')
def test_profile_returns_email(authn_policy, user_model):
    """The profile should include the user's email."""
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:foo@bar.com"
    user_model.get_by_id.return_value = FakeUser(email="foo@bar.com")

    result = ProfileController(request).profile()

    assert result["model"]["email"] == "foo@bar.com"


@pytest.mark.usefixtures('user_model')
def test_profile_returns_subscriptions(authn_policy, subscriptions_model):
    """The profile should include the user's subscriptions."""
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:foo@bar.com"
    subscriptions_model.get_subscriptions_for_uri.return_value = \
        {"some": "data"}

    result = ProfileController(request).profile()

    assert result["model"]["subscriptions"] == {"some": "data"}


def test_edit_profile_invalid_password(authn_policy, form_validator, user_model):
    """Make sure our edit_profile call validates the user password."""
    authn_policy.authenticated_userid.return_value = "johndoe"
    form_validator.return_value = (None, {
        "username": "john",
        "pwd": "blah",
        "subscriptions": "",
    })

    # Mock an invalid password
    user_model.validate_user.return_value = False

    request = DummyRequest(method='POST')
    profile = ProfileController(request)
    result = profile.edit_profile()

    assert result['code'] == 401
    assert any('pwd' in err for err in result['errors'])


def test_edit_profile_with_validation_failure(authn_policy, form_validator):
    """If form validation fails, return the error object."""
    authn_policy.authenticated_userid.return_value = "johndoe"
    form_validator.return_value = ({"errors": "BOOM!"}, None)

    request = DummyRequest(method='POST')
    profile = ProfileController(request)
    result = profile.edit_profile()

    assert result == {"errors": "BOOM!"}


def test_edit_profile_successfully(authn_policy, form_validator, user_model):
    """edit_profile() returns a dict with key "form" when successful."""
    authn_policy.authenticated_userid.return_value = "johndoe"
    form_validator.return_value = (None, {
        "username": "johndoe",
        "pwd": "password",
        "subscriptions": "",
    })
    user_model.validate_user.return_value = True
    user_model.get_by_id.return_value = FakeUser(email="john@doe.com")

    request = DummyRequest(method='POST')
    profile = ProfileController(request)
    result = profile.edit_profile()

    assert result == {"model": {"email": "john@doe.com"}}


def test_subscription_update(authn_policy, form_validator,
                             subscriptions_model, user_model):
    """Make sure that the new status is written into the DB."""
    authn_policy.authenticated_userid.return_value = "acct:john@doe"
    form_validator.return_value = (None, {
        "username": "acct:john@doe",
        "pwd": "smith",
        "subscriptions": '{"active":true,"uri":"acct:john@doe","id":1}',
    })
    mock_sub = Mock(active=False, uri="acct:john@doe")
    subscriptions_model.get_by_id.return_value = mock_sub
    user_model.get_by_id.return_value = FakeUser(email="john@doe")

    request = DummyRequest(method='POST')
    profile = ProfileController(request)
    result = profile.edit_profile()

    assert mock_sub.active is True
    assert result == {"model": {"email": "john@doe"}}


@pytest.mark.usefixtures('activation_model', 'dummy_db_session')
def test_disable_user_with_invalid_password(form_validator, user_model):
    """Make sure our disable_user call validates the user password."""
    request = DummyRequest(method='POST')
    form_validator.return_value = (None, {"username": "john", "pwd": "doe"})

    # With an invalid password, get_user returns None
    user_model.get_user.return_value = None

    profile = ProfileController(request)
    result = profile.disable_user()

    assert result['code'] == 401
    assert any('pwd' in err for err in result['errors'])


@pytest.mark.usefixtures('activation_model', 'dummy_db_session')
def test_disable_user_sets_random_password(form_validator, user_model):
    """Check if the user is disabled."""
    request = DummyRequest(method='POST')
    form_validator.return_value = (None, {"username": "john", "pwd": "doe"})

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
def pop_flash(request):
    patcher = patch('h.accounts.views.session.pop_flash', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def subscriptions_model(request):
    patcher = patch('h.accounts.views.Subscriptions', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def user_model(config, request):
    patcher = patch('h.accounts.views.User', autospec=True)
    request.addfinalizer(patcher.stop)
    user = patcher.start()
    config.registry.registerUtility(user, IUserClass)
    return user


@pytest.fixture
def activation_model(config, request):
    patcher = patch('h.accounts.views.Activation', autospec=True)
    request.addfinalizer(patcher.stop)
    activation = patcher.start()
    config.registry.registerUtility(activation, IActivationClass)
    return activation


@pytest.fixture
def form_validator(request):
    patcher = patch('h.accounts.views.validate_form', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
