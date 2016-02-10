# -*- coding: utf-8 -*-
# pylint: disable=no-self-use

import mock
from mock import patch, MagicMock
import pytest

import deform
from pyramid import httpexceptions
from pyramid.testing import DummyRequest as _DummyRequest

from h.conftest import DummyFeature
from h.conftest import DummySession

from h import accounts
from h.accounts.views import ActivateController
from h.accounts.views import AjaxAuthController
from h.accounts.views import AuthController
from h.accounts.views import ForgotPasswordController
from h.accounts.views import ResetPasswordController
from h.accounts.views import RegisterController
from h.accounts.views import ProfileController
from h.accounts.views import NotificationsController


class DummyRequest(_DummyRequest):
    def __init__(self, *args, **kwargs):
        params = {
            # Add a dummy database session to the request
            'db': DummySession(),
            # Add a dummy feature flag querier to the request
            'feature': DummyFeature(),
        }
        params.update(kwargs)
        super(DummyRequest, self).__init__(*args, **params)


class FakeSubscription(object):
    def __init__(self, type, active):
        self.type = type
        self.active = active


class FakeUser(object):
    def __init__(self, **kwargs):
        self.activation = None
        for k in kwargs:
            setattr(self, k, kwargs[k])


class FakeSerializer(object):
    def dumps(self, obj):
        return 'faketoken'

    def loads(self, token):
        return {'username': 'foo@bar.com'}


# A fake version of colander.Invalid
class FakeInvalid(object):
    def __init__(self, errors):
        self.errors = errors

    def asdict(self):
        return self.errors


def form_validating_to(appstruct):
    form = MagicMock()
    form.validate.return_value = appstruct
    form.render.return_value = 'valid form'
    return form


def invalid_form(errors=None):
    if errors is None:
        errors = {}
    invalid = FakeInvalid(errors)
    form = MagicMock()
    form.validate.side_effect = deform.ValidationFailure(None, None, invalid)
    form.render.return_value = 'invalid form'
    return form


def mock_flash_function():
    """Return a mock object with the same API as request.session.flash()."""
    return mock.create_autospec(DummyRequest().session.flash,
                                return_value=None)


@pytest.mark.usefixtures('routes_mapper')
def test_login_redirects_when_logged_in(authn_policy):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

    with pytest.raises(httpexceptions.HTTPFound):
        AuthController(request).post()


@pytest.mark.usefixtures('routes_mapper')
def test_login_redirects_to_next_param_when_logged_in(authn_policy):
    request = DummyRequest(params={'next': '/foo/bar'})
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

    with pytest.raises(httpexceptions.HTTPFound) as e:
        AuthController(request).post()

    assert e.value.location == '/foo/bar'


@pytest.mark.usefixtures('routes_mapper')
def test_login_returns_form_when_validation_fails(authn_policy):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = None  # Logged out
    controller = AuthController(request)
    controller.form = invalid_form()

    result = controller.post()

    assert result == {'form': 'invalid form'}


@pytest.mark.usefixtures('routes_mapper')
@patch('h.accounts.views.LoginEvent', autospec=True)
def test_login_no_event_when_validation_fails(loginevent,
                                              authn_policy,
                                              notify):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = None  # Logged out
    controller = AuthController(request)
    controller.form = invalid_form()

    controller.post()

    assert not loginevent.called
    assert not notify.called


@pytest.mark.usefixtures('routes_mapper')
def test_login_redirects_when_validation_succeeds(authn_policy):
    request = DummyRequest(auth_domain='hypothes.is')
    authn_policy.authenticated_userid.return_value = None  # Logged out
    controller = AuthController(request)
    controller.form = form_validating_to({"user": FakeUser(username='cara')})

    result = controller.post()

    assert isinstance(result, httpexceptions.HTTPFound)


@pytest.mark.usefixtures('routes_mapper')
def test_login_redirects_to_next_param_when_validation_succeeds(authn_policy):
    request = DummyRequest(
        params={'next': '/foo/bar'}, auth_domain='hypothes.is')
    authn_policy.authenticated_userid.return_value = None  # Logged out
    controller = AuthController(request)
    controller.form = form_validating_to({"user": FakeUser(username='cara')})

    result = controller.post()

    assert isinstance(result, httpexceptions.HTTPFound)
    assert result.location == '/foo/bar'


@pytest.mark.usefixtures('routes_mapper')
@patch('h.accounts.views.LoginEvent', autospec=True)
def test_login_event_when_validation_succeeds(loginevent,
                                              authn_policy,
                                              notify):
    request = DummyRequest(auth_domain='hypothes.is')
    authn_policy.authenticated_userid.return_value = None  # Logged out
    elephant = FakeUser(username='avocado')
    controller = AuthController(request)
    controller.form = form_validating_to({"user": elephant})

    controller.post()

    loginevent.assert_called_with(request, elephant)
    notify.assert_called_with(loginevent.return_value)


@pytest.mark.usefixtures('routes_mapper')
@patch('h.accounts.views.LogoutEvent', autospec=True)
def test_logout_event(logoutevent, authn_policy, notify):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

    result = AuthController(request).logout()

    logoutevent.assert_called_with(request)
    notify.assert_called_with(logoutevent.return_value)


@pytest.mark.usefixtures('routes_mapper')
def test_logout_invalidates_session(authn_policy):
    request = DummyRequest()
    request.session["foo"] = "bar"
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

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


@pytest.mark.usefixtures('routes_mapper', 'session')
def test_login_ajax_returns_status_okay_when_validation_succeeds():
    request = DummyRequest(json_body={}, auth_domain='hypothes.is')
    controller = AjaxAuthController(request)
    controller.form = form_validating_to({'user': FakeUser(username='bob')})

    result = controller.login()

    assert result['status'] == 'okay'


@pytest.mark.usefixtures('routes_mapper')
def test_login_ajax_raises_JSONError_on_non_json_body():
    request = mock.Mock(authenticated_user=mock.Mock(groups=[]))
    type(request).json_body = mock.PropertyMock(side_effect=ValueError)

    controller = AjaxAuthController(request)

    with pytest.raises(accounts.JSONError) as exc_info:
        controller.login()
        assert exc_info.value.message.startswith(
            'Could not parse request body as JSON: ')


@pytest.mark.usefixtures('routes_mapper')
def test_login_ajax_raises_JSONError_on_non_object_json():
    request = mock.Mock(
        authenticated_user=mock.Mock(groups=[]), json_body='foo')

    controller = AjaxAuthController(request)

    with pytest.raises(accounts.JSONError) as exc_info:
        controller.login()
        assert (
            exc_info.value.message == 'Request JSON body must have a ' +
                                      'top-level object')


@pytest.mark.usefixtures('routes_mapper', 'session')
@mock.patch('h.accounts.schemas.check_csrf_token')
def test_login_ajax_converts_non_string_usernames_to_strings(_):
    for input_, expected_output in ((None, ''), (23, '23'), (True, 'True')):
        request = DummyRequest(
            json_body={'username': input_, 'password': 'pass'},
            auth_domain='hypothes.is')
        controller = AjaxAuthController(request)
        controller.form.validate = mock.Mock(
            return_value={'user': mock.Mock()})

        controller.login()

        controller.form.validate.assert_called_once_with(
            [('username', expected_output), ('password', 'pass')])


@pytest.mark.usefixtures('routes_mapper', 'session')
@mock.patch('h.accounts.schemas.check_csrf_token')
def test_login_ajax_converts_non_string_passwords_to_strings(_):
    for input_, expected_output in ((None, ''), (23, '23'), (True, 'True')):
        request = DummyRequest(
            json_body={'username': 'user', 'password': input_},
            auth_domain='hypothes.is')
        controller = AjaxAuthController(request)
        controller.form.validate = mock.Mock(
            return_value={'user': mock.Mock()})

        controller.login()

        controller.form.validate.assert_called_once_with(
            [('username', 'user'), ('password', expected_output)])


@pytest.mark.usefixtures('routes_mapper')
def test_login_ajax_raises_ValidationFailure_on_ValidationFailure():
    controller = AjaxAuthController(DummyRequest(json_body={}))
    controller.form = invalid_form({'password': 'too short'})

    with pytest.raises(deform.ValidationFailure) as exc_info:
        controller.login()

    assert exc_info.value.error.asdict() == {'password': 'too short'}


@pytest.mark.usefixtures('routes_mapper', 'session')
def test_logout_ajax_returns_status_okay():
    request = DummyRequest()

    result = AjaxAuthController(request).logout()

    assert result['status'] == 'okay'


forgot_password_fixtures = pytest.mark.usefixtures('activation_model',
                                                   'authn_policy',
                                                   'mailer',
                                                   'routes_mapper')


@forgot_password_fixtures
def test_forgot_password_returns_form_when_validation_fails():
    request = DummyRequest(method='POST')
    controller = ForgotPasswordController(request)
    controller.form = invalid_form()

    result = controller.post()

    assert result == {'form': 'invalid form'}


@forgot_password_fixtures
def test_forgot_password_creates_no_activations_when_validation_fails(activation_model):
    request = DummyRequest(method='POST')
    controller = ForgotPasswordController(request)
    controller.form = invalid_form()

    controller.post()

    assert activation_model.call_count == 0


@patch('h.accounts.views.reset_password_link')
@forgot_password_fixtures
def test_forgot_password_generates_reset_link(reset_link):
    request = DummyRequest(method='POST')
    request.registry.password_reset_serializer = FakeSerializer()
    user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
    controller = ForgotPasswordController(request)
    controller.form = form_validating_to({"user": user})

    controller.post()

    reset_link.assert_called_with(request, "faketoken")


@patch('h.accounts.views.reset_password_email')
@patch('h.accounts.views.reset_password_link')
@forgot_password_fixtures
def test_forgot_password_generates_mail(reset_link,
                                        reset_mail,
                                        activation_model):
    request = DummyRequest(method='POST')
    request.registry.password_reset_serializer = FakeSerializer()
    user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
    controller = ForgotPasswordController(request)
    controller.form = form_validating_to({"user": user})
    reset_link.return_value = "http://example.com"
    reset_mail.return_value = {
        'recipients': [],
        'subject': '',
        'body': ''
    }

    controller.post()

    reset_mail.assert_called_with(user, "faketoken", "http://example.com")


@patch('h.accounts.views.reset_password_email')
@forgot_password_fixtures
def test_forgot_password_sends_mail(reset_mail, mailer):
    request = DummyRequest(method='POST')
    request.registry.password_reset_serializer = FakeSerializer()
    user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
    controller = ForgotPasswordController(request)
    controller.form = form_validating_to({"user": user})
    message = reset_mail.return_value
    reset_mail.return_value = {
        'recipients': ['giraffe@thezoo.org'],
        'subject': 'subject',
        'body': 'body'
    }

    controller.post()

    mailer.send.assert_called_once_with(request,
                                        recipients=['giraffe@thezoo.org'],
                                        subject='subject',
                                        body='body')


@forgot_password_fixtures
def test_forgot_password_redirects_on_success():
    request = DummyRequest(method='POST')
    request.registry.password_reset_serializer = FakeSerializer()
    user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
    controller = ForgotPasswordController(request)
    controller.form = form_validating_to({"user": user})

    result = controller.post()

    assert isinstance(result, httpexceptions.HTTPRedirection)


@pytest.mark.usefixtures('routes_mapper')
def test_forgot_password_form_redirects_when_logged_in(authn_policy):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

    with pytest.raises(httpexceptions.HTTPFound):
        ForgotPasswordController(request).get()


reset_password_fixtures = pytest.mark.usefixtures('routes_mapper')


@reset_password_fixtures
def test_reset_password_returns_form_when_validation_fails():
    request = DummyRequest(method='POST')
    controller = ResetPasswordController(request)
    controller.form = invalid_form()

    result = controller.post()

    assert result == {'form': 'invalid form'}


@reset_password_fixtures
def test_reset_password_sets_user_password_from_form():
    request = DummyRequest(method='POST')
    elephant = FakeUser(password='password1')
    controller = ResetPasswordController(request)
    controller.form = form_validating_to({'user': elephant,
                                          'password': 's3cure!'})

    controller.post()

    assert elephant.password == 's3cure!'


@patch('h.accounts.views.PasswordResetEvent', autospec=True)
@reset_password_fixtures
def test_reset_password_emits_event(event, notify):
    request = DummyRequest(method='POST')
    user = FakeUser(password='password1')
    controller = ResetPasswordController(request)
    controller.form = form_validating_to({'user': user,
                                          'password': 's3cure!'})

    controller.post()

    event.assert_called_with(request, user)
    notify.assert_called_with(event.return_value)


@reset_password_fixtures
def test_reset_password_redirects_on_success():
    request = DummyRequest(method='POST')
    user = FakeUser(password='password1')
    controller = ResetPasswordController(request)
    controller.form = form_validating_to({'user': user,
                                          'password': 's3cure!'})

    result = controller.post()

    assert isinstance(result, httpexceptions.HTTPRedirection)


register_fixtures = pytest.mark.usefixtures('activation_model',
                                            'authn_policy',
                                            'mailer',
                                            'notify',
                                            'routes_mapper',
                                            'user_model')

@register_fixtures
def test_register_returns_errors_when_validation_fails():
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = invalid_form()

    result = controller.post()

    assert result == {"form": "invalid form"}


@register_fixtures
def test_register_creates_user_from_form_data(user_model):
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = form_validating_to({
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
        "random_other_field": "something else",
    })

    controller.post()

    user_model.assert_called_with(username="bob",
                                  email="bob@example.com",
                                  password="s3crets")


@register_fixtures
def test_register_adds_new_user_to_session(user_model):
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = form_validating_to({
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })

    controller.post()

    assert user_model.return_value in request.db.added


@register_fixtures
def test_register_creates_new_activation(activation_model,
                                         user_model):
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = form_validating_to({
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })
    new_user = user_model.return_value

    controller.post()

    assert new_user.activation == activation_model.return_value


@patch('h.accounts.views.activation_email')
@register_fixtures
def test_register_generates_activation_email_from_user(activation_email,
                                                       user_model):
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = form_validating_to({
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })
    new_user = user_model.return_value
    activation_email.return_value = {
        'recipients': [],
        'subject': '',
        'body': ''
    }

    controller.post()

    activation_email.assert_called_once_with(request, new_user)


@patch('h.accounts.views.activation_email')
@register_fixtures
def test_register_sends_email(activation_email, mailer):
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = form_validating_to({
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })
    activation_email.return_value = {
        'recipients': ['bob@example.com'],
        'subject': 'subject',
        'body': 'body'
    }

    controller.post()

    mailer.send.assert_called_once_with(request,
                                        recipients=['bob@example.com'],
                                        subject='subject',
                                        body='body')


@patch('h.accounts.views.RegistrationEvent')
@register_fixtures
def test_register_no_event_when_validation_fails(event, notify):
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = invalid_form()

    controller.post()

    assert not event.called
    assert not notify.called


@patch('h.accounts.views.RegistrationEvent')
@register_fixtures
def test_register_event_when_validation_succeeds(event, notify, user_model):
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = form_validating_to({
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })
    new_user = user_model.return_value

    controller.post()

    event.assert_called_with(request, new_user)
    notify.assert_called_with(event.return_value)


@register_fixtures
def test_register_event_redirects_on_success():
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = form_validating_to({
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })

    result = controller.post()

    assert isinstance(result, httpexceptions.HTTPRedirection)


@pytest.mark.usefixtures('routes_mapper')
def test_register_form_redirects_when_logged_in(authn_policy):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"
    controller = RegisterController(request)


    with pytest.raises(httpexceptions.HTTPRedirection):
        controller.get()


activate_fixtures = pytest.mark.usefixtures('ActivationEvent',
                                            'activation_model',
                                            'notify',
                                            'routes_mapper',
                                            'user_model')


@activate_fixtures
def test_activate_404s_if_id_not_int():
    request = DummyRequest(matchdict={
        'id': 'abc',  # Not an int.
        'code': 'abc456'})

    with pytest.raises(httpexceptions.HTTPNotFound):
        ActivateController(request).get_when_not_logged_in()


@activate_fixtures
def test_activate_looks_up_activation_by_code(activation_model, user_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    user_model.get_by_activation.return_value.id = 123

    ActivateController(request).get_when_not_logged_in()

    activation_model.get_by_code.assert_called_with('abc456')


@activate_fixtures
def test_activate_redirects_if_activation_not_found(activation_model):
    """

    If the activation code doesn't match any activation then we redirect to the
    front page and flash a message suggesting that they may already be
    activated and can sign in.

    This happens if a user clicks on an activation link from an email after
    they've already been activated, for example.

    (This also happens if users visit a bogus activation URL, but we're happy
    to do this same redirect in that edge case.)

    """
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    request.session.flash = mock_flash_function()
    activation_model.get_by_code.return_value = None

    result = ActivateController(request).get_when_not_logged_in()

    assert isinstance(result, httpexceptions.HTTPFound)
    assert request.session.flash.call_count == 1
    assert request.session.flash.call_args[0][0].startswith(
        "We didn't recognize that activation link.")


@activate_fixtures
def test_activate_looks_up_user_by_activation(activation_model, user_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    user_model.get_by_activation.return_value.id = 123

    ActivateController(request).get_when_not_logged_in()

    user_model.get_by_activation.assert_called_once_with(
        activation_model.get_by_code.return_value)


@activate_fixtures
def test_activate_404s_if_user_not_found(user_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    user_model.get_by_activation.return_value = None

    with pytest.raises(httpexceptions.HTTPNotFound):
        ActivateController(request).get_when_not_logged_in()


@activate_fixtures
def test_activate_404s_if_user_id_does_not_match_user_from_hash(user_model):
    """

    We don't want to let a user with a valid hash activate a different user's
    account!

    """
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    user_model.get_by_activation.return_value.id = 2  # Not the same id.

    with pytest.raises(httpexceptions.HTTPNotFound):
        ActivateController(request).get_when_not_logged_in()


@activate_fixtures
def test_activate_successful_deletes_activation(user_model, activation_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    request.db.delete = mock.create_autospec(request.db.delete,
                                             return_value=None)
    user_model.get_by_activation.return_value.id = 123

    ActivateController(request).get_when_not_logged_in()

    request.db.delete.assert_called_once_with(
        activation_model.get_by_code.return_value)


@activate_fixtures
def test_activate_successful_flashes_message(user_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    request.session.flash = mock_flash_function()
    user_model.get_by_activation.return_value.id = 123

    ActivateController(request).get_when_not_logged_in()

    assert request.session.flash.call_count == 1
    assert request.session.flash.call_args[0][0].startswith(
        "Your account has been activated")


@activate_fixtures
def test_activate_successful_creates_ActivationEvent(user_model,
                                                     ActivationEvent):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    user_model.get_by_activation.return_value.id = 123

    ActivateController(request).get_when_not_logged_in()

    ActivationEvent.assert_called_once_with(
        request, user_model.get_by_activation.return_value)


@activate_fixtures
def test_activate_successful_notifies(user_model, notify, ActivationEvent):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    user_model.get_by_activation.return_value.id = 123

    ActivateController(request).get_when_not_logged_in()

    notify.assert_called_once_with(ActivationEvent.return_value)


activate_already_logged_in_fixtures = pytest.mark.usefixtures('routes_mapper')


@activate_already_logged_in_fixtures
def test_activate_already_logged_in_when_id_not_an_int():
    request = DummyRequest(matchdict={
        'id': 'abc',  # Not an int.
        'code': 'abc456'},
        authenticated_user=mock.Mock(id=123, spec=['id']))

    with pytest.raises(httpexceptions.HTTPNotFound):
        ActivateController(request).get_when_logged_in()


@activate_already_logged_in_fixtures
def test_activate_already_logged_in_to_same_account():
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'},
                           authenticated_user=mock.Mock(id=123, spec=['id']))
    request.session.flash = mock_flash_function()

    result = ActivateController(request).get_when_logged_in()

    assert isinstance(result, httpexceptions.HTTPFound)
    assert request.session.flash.call_count == 1
    assert request.session.flash.call_args[0][0].startswith(
        "Your account has been activated and you're now signed in")


@activate_already_logged_in_fixtures
def test_activate_already_logged_in_to_different_account():
    request = DummyRequest(
        matchdict={'id': '123', 'code': 'abc456'},
        authenticated_user=mock.Mock(
            id=124,  # Different user id.
            spec=['id']))
    request.session.flash = mock_flash_function()

    result = ActivateController(request).get_when_logged_in()

    assert isinstance(result, httpexceptions.HTTPFound)
    assert request.session.flash.call_count == 1
    assert request.session.flash.call_args[0][0].startswith(
        "You're already signed in to a different account")


profile_fixtures = pytest.mark.usefixtures('routes_mapper')


@profile_fixtures
def test_profile_form_404s_if_not_logged_in():
    request = DummyRequest(authenticated_user=None)

    with pytest.raises(httpexceptions.HTTPNotFound):
        ProfileController(request).profile_form()


@profile_fixtures
def test_profile_404s_if_not_logged_in():
    request = DummyRequest(authenticated_user=None)

    with pytest.raises(httpexceptions.HTTPNotFound):
        ProfileController(request).profile()


@profile_fixtures
def test_profile_400s_with_no_formid():
    user = FakeUser()
    request = DummyRequest(post={}, authenticated_user=user)

    with pytest.raises(httpexceptions.HTTPBadRequest):
        ProfileController(request).profile()


@profile_fixtures
def test_profile_400s_with_bogus_formid():
    user = FakeUser()
    request = DummyRequest(post={'__formid__': 'hax0rs'},
                           authenticated_user=user)

    with pytest.raises(httpexceptions.HTTPBadRequest):
        ProfileController(request).profile()


@profile_fixtures
def test_profile_changing_email_with_valid_data_updates_email():
    user = FakeUser(email=None, password=None)
    request = DummyRequest(post={'__formid__': 'email'},
                           authenticated_user=user)
    controller = ProfileController(request)
    controller.forms['email'] = form_validating_to({'email': 'amrit@example.com'})

    controller.profile()

    assert user.email == 'amrit@example.com'


@profile_fixtures
def test_profile_changing_email_with_valid_data_redirects():
    user = FakeUser(email=None, password=None)
    request = DummyRequest(post={'__formid__': 'email'},
                           authenticated_user=user)
    controller = ProfileController(request)
    controller.forms['email'] = form_validating_to({'email': 'amrit@example.com'})

    result = controller.profile()

    assert isinstance(result, httpexceptions.HTTPFound)


@profile_fixtures
def test_profile_changing_email_with_invalid_data_returns_form():
    user = FakeUser(email=None, password=None)
    request = DummyRequest(post={'__formid__': 'email'},
                           authenticated_user=user)
    controller = ProfileController(request)
    controller.forms['email'] = invalid_form()

    result = controller.profile()

    assert 'email_form' in result


@profile_fixtures
def test_profile_changing_email_with_invalid_data_does_not_update_email():
    user = FakeUser(email=None, password=None)
    request = DummyRequest(post={'__formid__': 'email'},
                           authenticated_user=user)
    controller = ProfileController(request)
    controller.forms['email'] = invalid_form()

    controller.profile()

    assert user.email is None


@profile_fixtures
def test_profile_changing_password_with_valid_data_updates_password():
    user = FakeUser(email=None, password=None)
    request = DummyRequest(post={'__formid__': 'password'},
                           authenticated_user=user)
    controller = ProfileController(request)
    controller.forms['password'] = form_validating_to({'new_password': 'secrets!'})

    controller.profile()

    assert user.password == 'secrets!'


@profile_fixtures
def test_profile_changing_password_with_valid_data_redirects():
    user = FakeUser(email=None, password=None)
    request = DummyRequest(post={'__formid__': 'password'},
                           authenticated_user=user)
    controller = ProfileController(request)
    controller.forms['password'] = form_validating_to({'new_password': 'secrets!'})

    result = controller.profile()

    assert isinstance(result, httpexceptions.HTTPFound)


@profile_fixtures
def test_profile_changing_password_with_invalid_data_returns_form():
    user = FakeUser(email=None, password=None)
    request = DummyRequest(post={'__formid__': 'password'},
                           authenticated_user=user)
    controller = ProfileController(request)
    controller.forms['password'] = invalid_form()

    result = controller.profile()

    assert 'password_form' in result


@profile_fixtures
def test_profile_changing_password_with_invalid_data_does_not_update_password():
    user = FakeUser(email=None, password=None)
    request = DummyRequest(post={'__formid__': 'password'},
                           authenticated_user=user)
    controller = ProfileController(request)
    controller.forms['password'] = invalid_form()

    controller.profile()

    assert user.password is None


notifications_fixtures = pytest.mark.usefixtures('authn_policy',
                                                 'routes_mapper',
                                                 'subscriptions_model')


@notifications_fixtures
def test_notifications_form_404s_if_not_logged_in(authn_policy):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = None

    with pytest.raises(httpexceptions.HTTPNotFound):
        NotificationsController(request).notifications_form()


@notifications_fixtures
def test_notifications_form_sets_subscriptions_data_in_form(authn_policy,
                                                            subscriptions_model):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = 'fiona'
    subscriptions_model.get_subscriptions_for_uri.return_value = [
        FakeSubscription('reply', True),
        FakeSubscription('foo', False),
    ]
    controller = NotificationsController(request)
    controller.form = form_validating_to({})

    controller.notifications_form()

    controller.form.set_appstruct.assert_called_once_with({
        'notifications': set(['reply']),
    })


@notifications_fixtures
def test_notifications_404s_if_not_logged_in():
    request = DummyRequest(post={})

    with pytest.raises(httpexceptions.HTTPNotFound):
        NotificationsController(request).notifications()


@notifications_fixtures
def test_notifications_with_invalid_data_returns_form(authn_policy):
    request = DummyRequest(post={})
    authn_policy.authenticated_userid.return_value = 'jerry'
    controller = NotificationsController(request)
    controller.form = invalid_form()

    result = controller.notifications()

    assert 'form' in result


@notifications_fixtures
def test_notifications_form_with_valid_data_updates_subscriptions(authn_policy,
                                                                  subscriptions_model):
    request = DummyRequest(post={})
    authn_policy.authenticated_userid.return_value = 'fiona'
    subs = [
        FakeSubscription('reply', True),
        FakeSubscription('foo', False),
    ]
    subscriptions_model.get_subscriptions_for_uri.return_value = subs
    controller = NotificationsController(request)
    controller.form = form_validating_to({
        'notifications': set(['foo'])
    })

    controller.notifications()

    assert subs[0].active == False
    assert subs[1].active == True


@notifications_fixtures
def test_notifications_form_with_valid_data_redirects(authn_policy,
                                                      subscriptions_model):
    request = DummyRequest(post={})
    authn_policy.authenticated_userid.return_value = 'fiona'
    subscriptions_model.get_subscriptions_for_uri.return_value = []
    controller = NotificationsController(request)
    controller.form = form_validating_to({})

    result = controller.notifications()

    assert isinstance(result, httpexceptions.HTTPFound)


@pytest.fixture
def pop_flash(request):
    patcher = patch('h.accounts.views.session.pop_flash', autospec=True)
    func = patcher.start()
    request.addfinalizer(patcher.stop)
    return func


@pytest.fixture
def session(request):
    patcher = patch('h.accounts.views.session', autospec=True)
    session = patcher.start()
    request.addfinalizer(patcher.stop)
    return session


@pytest.fixture
def subscriptions_model(request):
    patcher = patch('h.models.Subscriptions', autospec=True)
    model = patcher.start()
    request.addfinalizer(patcher.stop)
    return model


@pytest.fixture
def user_model(config, request):
    patcher = patch('h.accounts.views.User', autospec=True)
    model = patcher.start()
    request.addfinalizer(patcher.stop)
    return model


@pytest.fixture
def activation_model(config, request):
    patcher = patch('h.accounts.views.Activation', autospec=True)
    model = patcher.start()
    request.addfinalizer(patcher.stop)
    return model


@pytest.fixture
def ActivationEvent(config, request):
    patcher = patch('h.accounts.views.ActivationEvent', autospec=True)
    model = patcher.start()
    request.addfinalizer(patcher.stop)
    return model


@pytest.fixture
def mailer(request):
    patcher = patch('h.accounts.views.mailer', autospec=True)
    module = patcher.start()
    request.addfinalizer(patcher.stop)
    return module
