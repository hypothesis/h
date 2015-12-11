# -*- coding: utf-8 -*-
# pylint: disable=no-self-use

import mock
from mock import patch, Mock, MagicMock
import pytest

import deform
from pyramid import httpexceptions
from pyramid.testing import DummyRequest as _DummyRequest

from h.conftest import DummyFeature
from h.conftest import DummySession

from h import accounts
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


@pytest.mark.usefixtures('routes_mapper')
def test_login_redirects_when_logged_in(authn_policy):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

    with pytest.raises(httpexceptions.HTTPFound):
        AuthController(request).login()


@pytest.mark.usefixtures('routes_mapper')
def test_login_redirects_to_next_param_when_logged_in(authn_policy):
    request = DummyRequest(params={'next': '/foo/bar'})
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

    with pytest.raises(httpexceptions.HTTPFound) as e:
        AuthController(request).login()

    assert e.value.location == '/foo/bar'


@pytest.mark.usefixtures('routes_mapper')
def test_login_returns_form_when_validation_fails(authn_policy):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = None  # Logged out
    controller = AuthController(request)
    controller.form = invalid_form()

    result = controller.login()

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

    controller.login()

    assert not loginevent.called
    assert not notify.called


@pytest.mark.usefixtures('routes_mapper')
def test_login_redirects_when_validation_succeeds(authn_policy):
    request = DummyRequest(auth_domain='hypothes.is')
    authn_policy.authenticated_userid.return_value = None  # Logged out
    controller = AuthController(request)
    controller.form = form_validating_to({"user": FakeUser(username='cara')})

    result = controller.login()

    assert isinstance(result, httpexceptions.HTTPFound)


@pytest.mark.usefixtures('routes_mapper')
def test_login_redirects_to_next_param_when_validation_succeeds(authn_policy):
    request = DummyRequest(
        params={'next': '/foo/bar'}, auth_domain='hypothes.is')
    authn_policy.authenticated_userid.return_value = None  # Logged out
    controller = AuthController(request)
    controller.form = form_validating_to({"user": FakeUser(username='cara')})

    result = controller.login()

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

    controller.login()

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


@pytest.mark.usefixtures('routes_mapper')
def test_login_ajax_returns_status_okay_when_validation_succeeds():
    request = DummyRequest(json_body={}, auth_domain='hypothes.is')
    controller = AjaxAuthController(request)
    controller.form = form_validating_to({'user': FakeUser(username='bob')})

    result = controller.login()

    assert result['status'] == 'okay'


@pytest.mark.usefixtures('routes_mapper')
def test_login_ajax_returns_status_failure_on_validation_failure():
    request = DummyRequest(json_body={})
    controller = AjaxAuthController(request)
    controller.form = invalid_form({'password': 'too short'})

    result = controller.login()

    assert result['status'] == 'failure'
    assert result['errors'] == {'password': 'too short'}


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


@pytest.mark.usefixtures('routes_mapper')
@mock.patch('h.accounts.schemas.check_csrf_token')
def test_login_ajax_returns_status_failure_on_non_string_username(_):
    for username in (None, 23, True):
        request = DummyRequest(
            json_body={'username': username, 'password': 'pass'})

        controller = AjaxAuthController(request)

        result = controller.login()

        assert result['status'] == 'failure'
        assert result['errors']


@pytest.mark.usefixtures('routes_mapper')
@mock.patch('h.accounts.schemas.check_csrf_token')
def test_login_ajax_returns_status_failure_on_non_string_password(_):
    for password in (None, 23, True):
        request = DummyRequest(json_body={
            'username': 'user', 'password': password})

        controller = AjaxAuthController(request)

        result = controller.login()

        assert result['status'] == 'failure'
        assert result['errors']


@pytest.mark.usefixtures('routes_mapper')
def test_login_ajax_returns_status_failure_on_no_username():
    request = DummyRequest(json_body={'password': 'pass'})

    controller = AjaxAuthController(request)

    result = controller.login()

    assert result['status'] == 'failure'
    assert result['errors']['username']


@pytest.mark.usefixtures('routes_mapper')
def test_login_ajax_returns_status_failure_on_no_password():
    request = DummyRequest(json_body={'username': 'user'})

    controller = AjaxAuthController(request)

    result = controller.login()

    assert result['status'] == 'failure'
    assert result['errors']['password']


@pytest.mark.usefixtures('routes_mapper')
def test_logout_ajax_returns_status_okay():
    request = DummyRequest()

    result = AjaxAuthController(request).logout()

    assert result['status'] == 'okay'


forgot_password_fixtures = pytest.mark.usefixtures('activation_model',
                                                   'authn_policy',
                                                   'mailer',
                                                   'routes_mapper')


@forgot_password_fixtures
def test_forgot_password_returns_form_when_validation_fails(authn_policy):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    controller = ForgotPasswordController(request)
    controller.form = invalid_form()

    result = controller.forgot_password()

    assert result == {'form': 'invalid form'}


@forgot_password_fixtures
def test_forgot_password_creates_no_activations_when_validation_fails(activation_model,
                                                                      authn_policy):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    controller = ForgotPasswordController(request)
    controller.form = invalid_form()

    controller.forgot_password()

    assert activation_model.call_count == 0


@forgot_password_fixtures
def test_forgot_password_creates_activation_for_user(activation_model,
                                                     authn_policy):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    activation = activation_model.return_value
    user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
    controller = ForgotPasswordController(request)
    controller.form = form_validating_to({"user": user})

    controller.forgot_password()

    activation_model.assert_called_with()
    assert activation in request.db.added
    assert user.activation == activation


@patch('h.accounts.views.reset_password_link')
@forgot_password_fixtures
def test_forgot_password_generates_reset_link_from_activation(reset_link,
                                                              activation_model,
                                                              authn_policy):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
    controller = ForgotPasswordController(request)
    controller.form = form_validating_to({"user": user})
    activation_model.return_value.code = "abcde12345"

    controller.forgot_password()

    reset_link.assert_called_with(request, "abcde12345")


@patch('h.accounts.views.reset_password_email')
@patch('h.accounts.views.reset_password_link')
@forgot_password_fixtures
def test_forgot_password_generates_mail(reset_link,
                                        reset_mail,
                                        activation_model,
                                        authn_policy):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
    controller = ForgotPasswordController(request)
    controller.form = form_validating_to({"user": user})
    activation_model.return_value.code = "abcde12345"
    reset_link.return_value = "http://example.com"

    controller.forgot_password()

    reset_mail.assert_called_with(user, "abcde12345", "http://example.com")


@patch('h.accounts.views.reset_password_email')
@forgot_password_fixtures
def test_forgot_password_sends_mail(reset_mail, authn_policy, mailer):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
    controller = ForgotPasswordController(request)
    controller.form = form_validating_to({"user": user})
    message = reset_mail.return_value

    controller.forgot_password()

    assert message in mailer.outbox


@forgot_password_fixtures
def test_forgot_password_redirects_on_success(authn_policy):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
    controller = ForgotPasswordController(request)
    controller.form = form_validating_to({"user": user})

    result = controller.forgot_password()

    assert isinstance(result, httpexceptions.HTTPRedirection)


@pytest.mark.usefixtures('routes_mapper')
def test_forgot_password_form_redirects_when_logged_in(authn_policy):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

    with pytest.raises(httpexceptions.HTTPFound):
        ForgotPasswordController(request).forgot_password_form()


reset_password_fixtures = pytest.mark.usefixtures('routes_mapper')


@reset_password_fixtures
def test_reset_password_returns_form_when_validation_fails():
    request = DummyRequest(method='POST')
    controller = ResetPasswordController(request)
    controller.form = invalid_form()

    result = controller.reset_password()

    assert result == {'form': 'invalid form'}


@reset_password_fixtures
def test_reset_password_sets_user_password_from_form():
    request = DummyRequest(method='POST')
    elephant = FakeUser(password='password1')
    controller = ResetPasswordController(request)
    controller.form = form_validating_to({'user': elephant,
                                          'password': 's3cure!'})

    controller.reset_password()

    assert elephant.password == 's3cure!'


@reset_password_fixtures
def test_reset_password_deletes_activation():
    request = DummyRequest(method='POST')
    user = FakeUser(password='password1')
    user.activation = mock.sentinel.activation
    controller = ResetPasswordController(request)
    controller.form = form_validating_to({'user': user,
                                          'password': 's3cure!'})

    controller.reset_password()

    assert mock.sentinel.activation in request.db.deleted


@patch('h.accounts.views.PasswordResetEvent', autospec=True)
@reset_password_fixtures
def test_reset_password_emits_event(event, notify):
    request = DummyRequest(method='POST')
    user = FakeUser(password='password1')
    controller = ResetPasswordController(request)
    controller.form = form_validating_to({'user': user,
                                          'password': 's3cure!'})

    controller.reset_password()

    event.assert_called_with(request, user)
    notify.assert_called_with(event.return_value)


@reset_password_fixtures
def test_reset_password_redirects_on_success():
    request = DummyRequest(method='POST')
    user = FakeUser(password='password1')
    controller = ResetPasswordController(request)
    controller.form = form_validating_to({'user': user,
                                          'password': 's3cure!'})

    result = controller.reset_password()

    assert isinstance(result, httpexceptions.HTTPRedirection)


register_fixtures = pytest.mark.usefixtures('activation_model',
                                            'mailer',
                                            'notify',
                                            'routes_mapper',
                                            'user_model')

@register_fixtures
def test_register_returns_errors_when_validation_fails():
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = invalid_form()

    result = controller.register()

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

    controller.register()

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

    controller.register()

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

    controller.register()

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

    controller.register()

    activation_email.assert_called_with(request, new_user)


@patch('h.accounts.views.activation_email')
@register_fixtures
def test_register_sends_activation_email(activation_email,
                                         mailer):
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = form_validating_to({
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })

    controller.register()

    assert activation_email.return_value in mailer.outbox


@patch('h.accounts.views.RegistrationEvent')
@register_fixtures
def test_register_no_event_when_validation_fails(event, notify):
    request = DummyRequest(method='POST')
    controller = RegisterController(request)
    controller.form = invalid_form()

    controller.register()

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

    controller.register()

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

    result = controller.register()

    assert isinstance(result, httpexceptions.HTTPRedirection)


@pytest.mark.usefixtures('routes_mapper')
def test_register_form_redirects_when_logged_in(authn_policy):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"
    controller = RegisterController(request)


    with pytest.raises(httpexceptions.HTTPRedirection):
        controller.register_form()


activate_fixtures = pytest.mark.usefixtures('activation_model',
                                            'notify',
                                            'routes_mapper',
                                            'user_model')

@activate_fixtures
def test_activate_returns_not_found_if_code_missing():
    request = DummyRequest(matchdict={'id': '123'})

    result = RegisterController(request).activate()

    assert isinstance(result, httpexceptions.HTTPNotFound)


@activate_fixtures
def test_activate_returns_not_found_if_id_missing():
    request = DummyRequest(matchdict={'code': 'abc123'})

    result = RegisterController(request).activate()

    assert isinstance(result, httpexceptions.HTTPNotFound)


@activate_fixtures
def test_activate_returns_not_found_if_id_not_integer():
    request = DummyRequest(matchdict={'id': 'abc', 'code': 'abc456'})

    result = RegisterController(request).activate()

    assert isinstance(result, httpexceptions.HTTPNotFound)


@activate_fixtures
def test_activate_looks_up_activation_by_code(activation_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})

    result = RegisterController(request).activate()

    activation_model.get_by_code.assert_called_with('abc456')


@activate_fixtures
def test_activate_returns_not_found_if_activation_unknown(activation_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    activation_model.get_by_code.return_value = None

    result = RegisterController(request).activate()

    assert isinstance(result, httpexceptions.HTTPNotFound)


@activate_fixtures
def test_activate_looks_up_user_by_activation(activation_model, user_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    activation = activation_model.get_by_code.return_value

    result = RegisterController(request).activate()

    user_model.get_by_activation.assert_called_with(activation)


@activate_fixtures
def test_activate_returns_not_found_if_user_not_found(user_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    user_model.get_by_activation.return_value = None

    result = RegisterController(request).activate()

    assert isinstance(result, httpexceptions.HTTPNotFound)


@activate_fixtures
def test_activate_returns_not_found_if_userid_does_not_match(user_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    giraffe = FakeUser(id=456)
    user_model.get_by_activation.return_value = giraffe

    result = RegisterController(request).activate()

    assert isinstance(result, httpexceptions.HTTPNotFound)


@activate_fixtures
def test_activate_redirects_on_success(user_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    giraffe = FakeUser(id=123)
    user_model.get_by_activation.return_value = giraffe

    result = RegisterController(request).activate()

    assert isinstance(result, httpexceptions.HTTPRedirection)


@activate_fixtures
def test_activate_activates_user(activation_model, user_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    activation = activation_model.get_by_code.return_value
    giraffe = FakeUser(id=123)
    user_model.get_by_activation.return_value = giraffe

    result = RegisterController(request).activate()

    assert activation in request.db.deleted


@patch('h.accounts.views.ActivationEvent')
@activate_fixtures
def test_activate_no_event_on_failure(event, notify):
    request = DummyRequest()

    RegisterController(request).activate()

    assert not event.called
    assert not notify.called


@patch('h.accounts.views.ActivationEvent')
@activate_fixtures
def test_activate_event_when_validation_succeeds(event,
                                                 notify,
                                                 user_model):
    request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
    giraffe = FakeUser(id=123)
    user_model.get_by_activation.return_value = giraffe

    RegisterController(request).activate()

    event.assert_called_with(request, giraffe)
    notify.assert_called_with(event.return_value)


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
def test_notifications_404s_if_not_logged_in(authn_policy):
    request = DummyRequest(post={})
    authn_policy.authenticated_userid.return_value = None

    with pytest.raises(httpexceptions.HTTPNotFound):
        NotificationsController(request).notifications()


@notifications_fixtures
def test_notifications_with_invalid_data_returns_form():
    request = DummyRequest(post={})
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
