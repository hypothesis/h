# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
from collections import namedtuple

from mock import patch, Mock, MagicMock
import pytest

import deform
from pyramid import httpexceptions
from pyramid.testing import DummyRequest as _DummyRequest

from h.conftest import DummyFeature
from h.conftest import DummySession

from h.accounts.views import ajax_form
from h.accounts.views import validate_form
from h.accounts.views import AjaxAuthController
from h.accounts.views import AuthController
from h.accounts.views import ForgotPasswordController
from h.accounts.views import RegisterController
from h.accounts.views import ProfileController


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


class FakeUser(object):
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])


# A fake version of colander.Invalid for use when testing validate_form
class FakeInvalid(object):
    def __init__(self, errors):
        self.errors = errors

    def asdict(self):
        return self.errors


def form_validating_to(appstruct):
    form = Mock()
    form.validate.return_value = appstruct
    form.render.return_value = 'valid form'
    return form


def invalid_form(errors=None):
    if errors is None:
        errors = {}
    invalid = FakeInvalid(errors)
    form = Mock()
    form.validate.side_effect = deform.ValidationFailure(None, None, invalid)
    form.render.return_value = 'invalid form'
    return form


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
    result = ajax_form(request, {'errors': {}})

    assert result['status'] == 'failure'


def test_ajax_form_sets_status_code_400_on_errors():
    request = DummyRequest()
    _ = ajax_form(request, {'errors': {}})

    assert request.response.status_code == 400


def test_ajax_form_sets_status_code_from_input_on_errors():
    request = DummyRequest()
    _ = ajax_form(request, {'errors': {}, 'code': 418})

    assert request.response.status_code == 418


def test_ajax_form_passes_errors_through_on_errors():
    request = DummyRequest()
    errors = {
        '': 'Top level error',
        'name': 'Name is too weird',
        'email': 'Email must be @hotmail.com',
    }
    result = ajax_form(request, {'errors': errors})

    assert result['errors'] == {'': 'Top level error',
                                'name': 'Name is too weird',
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


def test_validate_form_passes_data_to_validate():
    form = MagicMock()

    _, _ = validate_form(form, {})

    form.validate.assert_called_with({})


def test_validate_form_failure():
    invalid = FakeInvalid({'': 'Asplode!', 'email': 'No @ sign!'})
    form = MagicMock()
    form.validate.side_effect = deform.ValidationFailure(None, None, invalid)

    err, data = validate_form(form, {})

    assert err == {'errors': {'': 'Asplode!', 'email': 'No @ sign!'}}
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

    with pytest.raises(httpexceptions.HTTPFound):
        AuthController(request).login()


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
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = None  # Logged out
    controller = AuthController(request)
    controller.form = form_validating_to({"user": FakeUser(username='cara')})

    result = controller.login()

    assert isinstance(result, httpexceptions.HTTPFound)


@pytest.mark.usefixtures('routes_mapper')
@patch('h.accounts.views.LoginEvent', autospec=True)
def test_login_event_when_validation_succeeds(loginevent,
                                              authn_policy,
                                              notify):
    request = DummyRequest()
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
    request = DummyRequest(json_body={})
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
def test_logout_ajax_returns_status_okay():
    request = DummyRequest()

    result = AjaxAuthController(request).logout()

    assert result['status'] == 'okay'


forgot_password_fixtures = pytest.mark.usefixtures('activation_model',
                                                   'authn_policy',
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

    user_model.get_by_email.assert_called_with("giraffe@thezoo.org")


@forgot_password_fixtures
def test_forgot_password_creates_activation_for_user(activation_model,
                                                     authn_policy,
                                                     form_validator,
                                                     user_model):
    request = DummyRequest(method='POST')
    authn_policy.authenticated_userid.return_value = None
    form_validator.return_value = (None, {"email": "giraffe@thezoo.org"})

    ForgotPasswordController(request).forgot_password()


    user = user_model.get_by_email.return_value
    activation = activation_model.return_value

    activation_model.assert_called_with()
    assert activation in request.db.added
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

    activation_model.get_by_code.assert_called_with('abc123')


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

    user_model.get_by_activation.assert_called_with(activation)


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
def test_reset_password_deletes_activation(activation_model, form_validator):
    request = DummyRequest(method='POST',
                           matchdict={'code': 'abc123'})
    form_validator.return_value = (None, {"password": "s3cure!"})
    activation = activation_model.get_by_code.return_value

    ForgotPasswordController(request).reset_password()

    assert activation in request.db.deleted


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


register_fixtures = pytest.mark.usefixtures('activation_model',
                                            'form_validator',
                                            'mailer',
                                            'notify',
                                            'routes_mapper',
                                            'user_model')

@register_fixtures
def test_register_returns_errors_when_validation_fails(form_validator):
    request = DummyRequest(method='POST')
    form_validator.return_value = ({"errors": "BANG!"}, None)

    result = RegisterController(request).register()

    assert result == {"errors": "BANG!"}


@register_fixtures
def test_register_creates_user_from_form_data(form_validator, user_model):
    request = DummyRequest(method='POST')
    form_validator.return_value = (None, {
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
        "random_other_field": "something else",
    })

    RegisterController(request).register()

    user_model.assert_called_with(username="bob",
                                  email="bob@example.com",
                                  password="s3crets")


@register_fixtures
def test_register_adds_new_user_to_session(form_validator, user_model):
    request = DummyRequest(method='POST')
    form_validator.return_value = (None, {
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })

    RegisterController(request).register()

    assert user_model.return_value in request.db.added


@register_fixtures
def test_register_creates_new_activation(activation_model,
                                         form_validator,
                                         user_model):
    request = DummyRequest(method='POST')
    form_validator.return_value = (None, {
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })
    new_user = user_model.return_value

    RegisterController(request).register()

    assert new_user.activation == activation_model.return_value


@patch('h.accounts.views.activation_email')
@register_fixtures
def test_register_generates_activation_email_from_user(activation_email,
                                                       form_validator,
                                                       user_model):
    request = DummyRequest(method='POST')
    form_validator.return_value = (None, {
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })
    new_user = user_model.return_value

    RegisterController(request).register()

    activation_email.assert_called_with(request, new_user)


@patch('h.accounts.views.activation_email')
@register_fixtures
def test_register_sends_activation_email(activation_email,
                                         form_validator,
                                         mailer):
    request = DummyRequest(method='POST')
    form_validator.return_value = (None, {
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })

    RegisterController(request).register()

    assert activation_email.return_value in mailer.outbox


@patch('h.accounts.views.RegistrationEvent')
@register_fixtures
def test_register_no_event_when_validation_fails(event,
                                                 form_validator,
                                                 notify):
    request = DummyRequest(method='POST')
    form_validator.return_value = ({"errors": "Kablooey!"}, None)

    RegisterController(request).register()

    assert not event.called
    assert not notify.called


@patch('h.accounts.views.RegistrationEvent')
@register_fixtures
def test_register_event_when_validation_succeeds(event,
                                                 form_validator,
                                                 notify,
                                                 user_model):
    request = DummyRequest(method='POST')
    form_validator.return_value = (None, {
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })
    new_user = user_model.return_value

    RegisterController(request).register()

    event.assert_called_with(request, new_user)
    notify.assert_called_with(event.return_value)


@register_fixtures
def test_register_event_redirects_on_success(form_validator):
    request = DummyRequest(method='POST')
    form_validator.return_value = (None, {
        "username": "bob",
        "email": "bob@example.com",
        "password": "s3crets",
    })

    result = RegisterController(request).register()

    assert isinstance(result, httpexceptions.HTTPRedirection)


@pytest.mark.usefixtures('routes_mapper')
def test_register_form_redirects_when_logged_in(authn_policy):
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

    result = RegisterController(request).register_form()

    assert isinstance(result, httpexceptions.HTTPRedirection)


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


@pytest.mark.usefixtures('subscriptions_model')
def test_profile_looks_up_by_logged_in_user(authn_policy, user_model):
    """
    When fetching the profile, look up email for the logged in user.

    (And don't, for example, use a 'username' passed to us in params.)
    """
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:foo@bar.com"

    ProfileController(request).profile()

    user_model.get_by_userid.assert_called_with(request.domain, "acct:foo@bar.com")


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
        "acct:foo@bar.com")


@pytest.mark.usefixtures('subscriptions_model')
def test_profile_returns_email(authn_policy, user_model):
    """The profile should include the user's email."""
    request = DummyRequest()
    authn_policy.authenticated_userid.return_value = "acct:foo@bar.com"
    user_model.get_by_userid.return_value = FakeUser(email="foo@bar.com")

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
    user_model.get_by_userid.return_value = FakeUser(email="john@doe.com")

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
    user_model.get_by_userid.return_value = FakeUser(email="john@doe")

    request = DummyRequest(method='POST')
    profile = ProfileController(request)
    result = profile.edit_profile()

    assert mock_sub.active is True
    assert result == {"model": {"email": "john@doe"}}


@pytest.mark.usefixtures('activation_model')
def test_disable_user_with_invalid_password(form_validator, user_model):
    """Make sure our disable_user call validates the user password."""
    request = Mock(method='POST', authenticated_userid='john')
    form_validator.return_value = (None, {"username": "john", "pwd": "doe"})

    # With an invalid password, validate_user() returns False.
    user_model.validate_user.return_value = False

    profile = ProfileController(request)
    result = profile.disable_user()

    assert result['code'] == 401
    assert any('pwd' in err for err in result['errors'])


@pytest.mark.usefixtures('activation_model')
def test_disable_user_sets_random_password(form_validator, user_model):
    """Check if the user is disabled."""
    request = Mock(method='POST', authenticated_userid='john')
    form_validator.return_value = (None, {"username": "john", "pwd": "doe"})

    user = FakeUser(password='abc')
    user_model.get_by_userid.return_value = user

    profile = ProfileController(request)
    profile.disable_user()

    assert user.password == user_model.generate_random_password.return_value


def test_disable_user_with_no_authenticated_user():
    exc = ProfileController(Mock(authenticated_userid=None)).disable_user()

    assert isinstance(exc, httpexceptions.HTTPUnauthorized)


@patch('h.accounts.views.Subscriptions')
def test_unsubscribe_sets_active_to_False(Subscriptions):
    """It sets the active field of the subscription to False."""
    Subscriptions.get_by_id.return_value = Mock(
        uri='acct:bob@hypothes.is', active=True)
    request = MagicMock(
        authenticated_userid='acct:bob@hypothes.is',
        GET={'subscription_id': 'subscription_id'}
    )

    ProfileController(request).unsubscribe()

    assert Subscriptions.get_by_id.return_value.active is False


@patch('h.accounts.views.Subscriptions')
def test_unsubscribe_not_authorized(Subscriptions):
    """If you try to unsubscribe someone else's subscription you get a 401."""
    Subscriptions.get_by_id.return_value = Mock(
        uri='acct:bob@hypothes.is', active=True)
    request = MagicMock(
        authenticated_userid='acct:fred@hypothes.is',
        GET={'subscription_id': 'subscription_id'}
    )

    with pytest.raises(httpexceptions.HTTPUnauthorized):
        ProfileController(request).unsubscribe()

    assert Subscriptions.get_by_id.return_value.active is True


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
    return patcher.start()


@pytest.fixture
def activation_model(config, request):
    patcher = patch('h.accounts.views.Activation', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def form_validator(request):
    patcher = patch('h.accounts.views.validate_form', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
