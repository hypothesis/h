# -*- coding: utf-8 -*-
# pylint: disable=no-self-use

import mock
import pytest

import deform
from pyramid import httpexceptions
from pyramid import testing

from h import conftest

from h import accounts
from h.accounts import views
from h.api.models.token import API_TOKEN_PREFIX


class DummyRequest(testing.DummyRequest):
    def __init__(self, *args, **kwargs):
        params = {
            # Add a dummy database session to the request
            'db': conftest.DummySession(),
            # Add a dummy feature flag querier to the request
            'feature': conftest.DummyFeature(),
        }
        params.update(kwargs)
        super(DummyRequest, self).__init__(*args, **params)


class FakeSubscription(object):
    def __init__(self, type_, active):
        self.type = type_
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
    form = mock.MagicMock()
    form.validate.return_value = appstruct
    form.render.return_value = 'valid form'
    return form


def invalid_form(errors=None):
    if errors is None:
        errors = {}
    invalid = FakeInvalid(errors)
    form = mock.MagicMock()
    form.validate.side_effect = deform.ValidationFailure(None, None, invalid)
    form.render.return_value = 'invalid form'
    return form


def mock_flash_function():
    """Return a mock object with the same API as request.session.flash()."""
    return mock.create_autospec(DummyRequest().session.flash,
                                return_value=None)


@pytest.mark.usefixtures('routes_mapper')
class TestAuthController(object):

    def test_post_redirects_when_logged_in(self, authn_policy):
        request = DummyRequest()
        authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

        with pytest.raises(httpexceptions.HTTPFound):
            views.AuthController(request).post()

    def test_post_redirects_to_next_param_when_logged_in(self, authn_policy):
        request = DummyRequest(params={'next': '/foo/bar'})
        authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

        with pytest.raises(httpexceptions.HTTPFound) as e:
            views.AuthController(request).post()

        assert e.value.location == '/foo/bar'

    def test_post_returns_form_when_validation_fails(self, authn_policy):
        request = DummyRequest()
        authn_policy.authenticated_userid.return_value = None  # Logged out
        controller = views.AuthController(request)
        controller.form = invalid_form()

        result = controller.post()

        assert result == {'form': 'invalid form'}

    @mock.patch('h.accounts.views.LoginEvent', autospec=True)
    def test_post_no_event_when_validation_fails(self,
                                                 loginevent,
                                                 authn_policy,
                                                 notify):
        request = DummyRequest()
        authn_policy.authenticated_userid.return_value = None  # Logged out
        controller = views.AuthController(request)
        controller.form = invalid_form()

        controller.post()

        assert not loginevent.called
        assert not notify.called

    def test_post_redirects_when_validation_succeeds(self, authn_policy):
        request = DummyRequest(auth_domain='hypothes.is')
        authn_policy.authenticated_userid.return_value = None  # Logged out
        controller = views.AuthController(request)
        controller.form = form_validating_to(
            {"user": FakeUser(username='cara')})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPFound)

    def test_post_redirects_to_next_param_when_validation_succeeds(
            self,
            authn_policy):
        request = DummyRequest(
            params={'next': '/foo/bar'}, auth_domain='hypothes.is')
        authn_policy.authenticated_userid.return_value = None  # Logged out
        controller = views.AuthController(request)
        controller.form = form_validating_to(
            {"user": FakeUser(username='cara')})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPFound)
        assert result.location == '/foo/bar'

    @mock.patch('h.accounts.views.LoginEvent', autospec=True)
    def test_post_event_when_validation_succeeds(self,
                                                 loginevent,
                                                 authn_policy,
                                                 notify):
        request = DummyRequest(auth_domain='hypothes.is')
        authn_policy.authenticated_userid.return_value = None  # Logged out
        elephant = FakeUser(username='avocado')
        controller = views.AuthController(request)
        controller.form = form_validating_to({"user": elephant})

        controller.post()

        loginevent.assert_called_with(request, elephant)
        notify.assert_called_with(loginevent.return_value)

    @mock.patch('h.accounts.views.LogoutEvent', autospec=True)
    def test_logout_event(self, logoutevent, authn_policy, notify):
        request = DummyRequest()
        authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

        views.AuthController(request).logout()

        logoutevent.assert_called_with(request)
        notify.assert_called_with(logoutevent.return_value)

    def test_logout_invalidates_session(self, authn_policy):
        request = DummyRequest()
        request.session["foo"] = "bar"
        authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

        views.AuthController(request).logout()

        assert "foo" not in request.session

    def test_logout_redirects(self):
        request = DummyRequest()

        result = views.AuthController(request).logout()

        assert isinstance(result, httpexceptions.HTTPFound)

    def test_logout_forgets_authenticated_user(self, authn_policy):
        request = DummyRequest()

        views.AuthController(request).logout()

        authn_policy.forget.assert_called_with(request)

    def test_logout_response_has_forget_headers(self, authn_policy):
        request = DummyRequest()
        authn_policy.forget.return_value = {
            'x-erase-fingerprints': 'on the hob'}

        result = views.AuthController(request).logout()

        assert result.headers['x-erase-fingerprints'] == 'on the hob'


@pytest.mark.usefixtures('routes_mapper',
                         'session')
class TestAjaxAuthController(object):

    def test_login_returns_status_okay_when_validation_succeeds(self):
        request = DummyRequest(json_body={}, auth_domain='hypothes.is')
        controller = views.AjaxAuthController(request)
        controller.form = form_validating_to(
            {'user': FakeUser(username='bob')})

        result = controller.login()

        assert result['status'] == 'okay'

    def test_login_raises_JSONError_on_non_json_body(self):
        request = mock.Mock(authenticated_user=mock.Mock(groups=[]))
        type(request).json_body = mock.PropertyMock(side_effect=ValueError)

        controller = views.AjaxAuthController(request)

        with pytest.raises(accounts.JSONError) as exc_info:
            controller.login()
            assert exc_info.value.message.startswith(
                'Could not parse request body as JSON: ')

    def test_login_raises_JSONError_on_non_object_json(self):
        request = mock.Mock(
            authenticated_user=mock.Mock(groups=[]), json_body='foo')

        controller = views.AjaxAuthController(request)

        with pytest.raises(accounts.JSONError) as exc_info:
            controller.login()
            assert (
                exc_info.value.message == 'Request JSON body must have a ' +
                                        'top-level object')

    @mock.patch('h.accounts.schemas.check_csrf_token')
    def test_login_converts_non_string_usernames_to_strings(self, _):
        for input_, expected_output in ((None, ''),
                                        (23, '23'),
                                        (True, 'True')):
            request = DummyRequest(
                json_body={'username': input_, 'password': 'pass'},
                auth_domain='hypothes.is')
            controller = views.AjaxAuthController(request)
            controller.form.validate = mock.Mock(
                return_value={'user': mock.Mock()})

            controller.login()

            controller.form.validate.assert_called_once_with(
                [('username', expected_output), ('password', 'pass')])

    @mock.patch('h.accounts.schemas.check_csrf_token')
    def test_login_converts_non_string_passwords_to_strings(self, _):
        for input_, expected_output in ((None, ''),
                                        (23, '23'),
                                        (True, 'True')):
            request = DummyRequest(
                json_body={'username': 'user', 'password': input_},
                auth_domain='hypothes.is')
            controller = views.AjaxAuthController(request)
            controller.form.validate = mock.Mock(
                return_value={'user': mock.Mock()})

            controller.login()

            controller.form.validate.assert_called_once_with(
                [('username', 'user'), ('password', expected_output)])

    def test_login_raises_ValidationFailure_on_ValidationFailure(self):
        controller = views.AjaxAuthController(DummyRequest(json_body={}))
        controller.form = invalid_form({'password': 'too short'})

        with pytest.raises(deform.ValidationFailure) as exc_info:
            controller.login()

        assert exc_info.value.error.asdict() == {'password': 'too short'}

    def test_logout_returns_status_okay(self):
        request = DummyRequest()

        result = views.AjaxAuthController(request).logout()

        assert result['status'] == 'okay'


@pytest.mark.usefixtures('activation_model',
                         'authn_policy',
                         'mailer',
                         'routes_mapper')
class TestForgotPasswordController(object):

    def test_post_returns_form_when_validation_fails(self):
        request = DummyRequest(method='POST')
        controller = views.ForgotPasswordController(request)
        controller.form = invalid_form()

        result = controller.post()

        assert result == {'form': 'invalid form'}

    def test_post_creates_no_activations_when_validation_fails(
            self,
            activation_model):
        request = DummyRequest(method='POST')
        controller = views.ForgotPasswordController(request)
        controller.form = invalid_form()

        controller.post()

        assert activation_model.call_count == 0

    @mock.patch('h.accounts.views.reset_password_link')
    def test_post_generates_reset_link(self, reset_link):
        request = DummyRequest(method='POST')
        request.registry.password_reset_serializer = FakeSerializer()
        user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
        controller = views.ForgotPasswordController(request)
        controller.form = form_validating_to({"user": user})

        controller.post()

        reset_link.assert_called_with(request, "faketoken")

    @mock.patch('h.accounts.views.reset_password_email')
    @mock.patch('h.accounts.views.reset_password_link')
    def test_post_generates_mail(self,
                                 reset_link,
                                 reset_mail,
                                 activation_model):
        request = DummyRequest(method='POST')
        request.registry.password_reset_serializer = FakeSerializer()
        user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
        controller = views.ForgotPasswordController(request)
        controller.form = form_validating_to({"user": user})
        reset_link.return_value = "http://example.com"
        reset_mail.return_value = {
            'recipients': [],
            'subject': '',
            'body': ''
        }

        controller.post()

        reset_mail.assert_called_with(user, "faketoken", "http://example.com")

    @mock.patch('h.accounts.views.reset_password_email')
    def test_post_sends_mail(self, reset_mail, mailer):
        request = DummyRequest(method='POST')
        request.registry.password_reset_serializer = FakeSerializer()
        user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
        controller = views.ForgotPasswordController(request)
        controller.form = form_validating_to({"user": user})
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

    def test_post_redirects_on_success(self):
        request = DummyRequest(method='POST')
        request.registry.password_reset_serializer = FakeSerializer()
        user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
        controller = views.ForgotPasswordController(request)
        controller.form = form_validating_to({"user": user})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPRedirection)

    def test_get_redirects_when_logged_in(self, authn_policy):
        request = DummyRequest(method='POST')
        authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"

        with pytest.raises(httpexceptions.HTTPFound):
            views.ForgotPasswordController(request).get()


@pytest.mark.usefixtures('routes_mapper')
class TestResetPasswordController(object):

    def test_post_returns_form_when_validation_fails(self):
        request = DummyRequest(method='POST')
        controller = views.ResetPasswordController(request)
        controller.form = invalid_form()

        result = controller.post()

        assert result == {'form': 'invalid form'}

    def test_post_sets_user_password_from_form(self):
        request = DummyRequest(method='POST')
        elephant = FakeUser(password='password1')
        controller = views.ResetPasswordController(request)
        controller.form = form_validating_to({'user': elephant,
                                              'password': 's3cure!'})

        controller.post()

        assert elephant.password == 's3cure!'

    @mock.patch('h.accounts.views.PasswordResetEvent', autospec=True)
    def test_post_emits_event(self, event, notify):
        request = DummyRequest(method='POST')
        user = FakeUser(password='password1')
        controller = views.ResetPasswordController(request)
        controller.form = form_validating_to({'user': user,
                                              'password': 's3cure!'})

        controller.post()

        event.assert_called_with(request, user)
        notify.assert_called_with(event.return_value)

    def test_post_redirects_on_success(self):
        request = DummyRequest(method='POST')
        user = FakeUser(password='password1')
        controller = views.ResetPasswordController(request)
        controller.form = form_validating_to({'user': user,
                                              'password': 's3cure!'})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPRedirection)


@pytest.mark.usefixtures('activation_model',
                         'authn_policy',
                         'mailer',
                         'notify',
                         'routes_mapper',
                         'user_model')
class TestRegisterController(object):

    def test_post_returns_errors_when_validation_fails(self):
        request = DummyRequest(method='POST')
        controller = views.RegisterController(request)
        controller.form = invalid_form()

        result = controller.post()

        assert result == {"form": "invalid form"}

    def test_post_creates_user_from_form_data(self, user_model):
        request = DummyRequest(method='POST')
        controller = views.RegisterController(request)
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

    def test_post_adds_new_user_to_session(self, user_model):
        request = DummyRequest(method='POST')
        controller = views.RegisterController(request)
        controller.form = form_validating_to({
            "username": "bob",
            "email": "bob@example.com",
            "password": "s3crets",
        })

        controller.post()

        assert user_model.return_value in request.db.added

    def test_post_creates_new_activation(self, activation_model, user_model):
        request = DummyRequest(method='POST')
        controller = views.RegisterController(request)
        controller.form = form_validating_to({
            "username": "bob",
            "email": "bob@example.com",
            "password": "s3crets",
        })
        new_user = user_model.return_value

        controller.post()

        assert new_user.activation == activation_model.return_value

    @mock.patch('h.accounts.views.activation_email')
    def test_post_generates_activation_email_from_user(self,
                                                       activation_email,
                                                       user_model):
        request = DummyRequest(method='POST')
        controller = views.RegisterController(request)
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

    @mock.patch('h.accounts.views.activation_email')
    def test_post_sends_email(self, activation_email, mailer):
        request = DummyRequest(method='POST')
        controller = views.RegisterController(request)
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

    @mock.patch('h.accounts.views.RegistrationEvent')
    def test_post_no_event_when_validation_fails(self, event, notify):
        request = DummyRequest(method='POST')
        controller = views.RegisterController(request)
        controller.form = invalid_form()

        controller.post()

        assert not event.called
        assert not notify.called

    @mock.patch('h.accounts.views.RegistrationEvent')
    def test_post_event_when_validation_succeeds(self,
                                                 event,
                                                 notify,
                                                 user_model):
        request = DummyRequest(method='POST')
        controller = views.RegisterController(request)
        controller.form = form_validating_to({
            "username": "bob",
            "email": "bob@example.com",
            "password": "s3crets",
        })
        new_user = user_model.return_value

        controller.post()

        event.assert_called_with(request, new_user)
        notify.assert_called_with(event.return_value)

    def test_post_event_redirects_on_success(self):
        request = DummyRequest(method='POST')
        controller = views.RegisterController(request)
        controller.form = form_validating_to({
            "username": "bob",
            "email": "bob@example.com",
            "password": "s3crets",
        })

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPRedirection)

    def test_get_redirects_when_logged_in(self, authn_policy):
        request = DummyRequest()
        authn_policy.authenticated_userid.return_value = "acct:jane@doe.org"
        controller = views.RegisterController(request)

        with pytest.raises(httpexceptions.HTTPRedirection):
            controller.get()


@pytest.mark.usefixtures('ActivationEvent',
                         'activation_model',
                         'notify',
                         'routes_mapper',
                         'user_model')
class TestActivateController(object):

    def test_get_when_not_logged_in_404s_if_id_not_int(self):
        request = DummyRequest(matchdict={
            'id': 'abc',  # Not an int.
            'code': 'abc456'})

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(request).get_when_not_logged_in()

    def test_get_when_not_logged_in_looks_up_activation_by_code(
            self,
            activation_model,
            user_model):
        request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(request).get_when_not_logged_in()

        activation_model.get_by_code.assert_called_with('abc456')

    def test_get_when_not_logged_in_redirects_if_activation_not_found(
            self,
            activation_model):
        """

        If the activation code doesn't match any activation then we redirect to
        the front page and flash a message suggesting that they may already be
        activated and can sign in.

        This happens if a user clicks on an activation link from an email after
        they've already been activated, for example.

        (This also happens if users visit a bogus activation URL, but we're
        happy to do this same redirect in that edge case.)

        """
        request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
        request.session.flash = mock_flash_function()
        activation_model.get_by_code.return_value = None

        result = views.ActivateController(request).get_when_not_logged_in()

        assert isinstance(result, httpexceptions.HTTPFound)
        assert request.session.flash.call_count == 1
        assert request.session.flash.call_args[0][0].startswith(
            "We didn't recognize that activation link.")

    def test_get_when_not_logged_in_looks_up_user_by_activation(
            self,
            activation_model,
            user_model):
        request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(request).get_when_not_logged_in()

        user_model.get_by_activation.assert_called_once_with(
            activation_model.get_by_code.return_value)

    def test_get_when_not_logged_in_404s_if_user_not_found(self, user_model):
        request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
        user_model.get_by_activation.return_value = None

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(request).get_when_not_logged_in()

    def test_get_when_not_logged_in_404s_if_user_id_does_not_match_hash(
            self,
            user_model):
        """

        We don't want to let a user with a valid hash activate a different
        user's account!

        """
        request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
        user_model.get_by_activation.return_value.id = 2  # Not the same id.

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(request).get_when_not_logged_in()

    def test_get_when_not_logged_in_successful_deletes_activation(
            self,
            user_model,
            activation_model):
        request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
        request.db.delete = mock.create_autospec(request.db.delete,
                                                 return_value=None)
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(request).get_when_not_logged_in()

        request.db.delete.assert_called_once_with(
            activation_model.get_by_code.return_value)

    def test_get_when_not_logged_in_successful_flashes_message(self,
                                                               user_model):
        request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
        request.session.flash = mock_flash_function()
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(request).get_when_not_logged_in()

        assert request.session.flash.call_count == 1
        assert request.session.flash.call_args[0][0].startswith(
            "Your account has been activated")

    def test_get_when_not_logged_in_successful_creates_ActivationEvent(
            self,
            user_model,
            ActivationEvent):
        request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(request).get_when_not_logged_in()

        ActivationEvent.assert_called_once_with(
            request, user_model.get_by_activation.return_value)

    def test_get_when_not_logged_in_successful_notifies(self,
                                                        user_model,
                                                        notify,
                                                        ActivationEvent):
        request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'})
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(request).get_when_not_logged_in()

        notify.assert_called_once_with(ActivationEvent.return_value)

    def test_get_when_logged_in_already_logged_in_when_id_not_an_int(self):
        request = DummyRequest(matchdict={
            'id': 'abc',  # Not an int.
            'code': 'abc456'},
            authenticated_user=mock.Mock(id=123, spec=['id']))

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(request).get_when_logged_in()

    def test_get_when_logged_in_already_logged_in_to_same_account(self):
        request = DummyRequest(matchdict={'id': '123', 'code': 'abc456'},
                               authenticated_user=mock.Mock(id=123,
                                                            spec=['id']))
        request.session.flash = mock_flash_function()

        result = views.ActivateController(request).get_when_logged_in()

        assert isinstance(result, httpexceptions.HTTPFound)
        assert request.session.flash.call_count == 1
        assert request.session.flash.call_args[0][0].startswith(
            "Your account has been activated and you're now signed in")

    def test_get_when_logged_in_already_logged_in_to_different_account(self):
        request = DummyRequest(
            matchdict={'id': '123', 'code': 'abc456'},
            authenticated_user=mock.Mock(
                id=124,  # Different user id.
                spec=['id']))
        request.session.flash = mock_flash_function()

        result = views.ActivateController(request).get_when_logged_in()

        assert isinstance(result, httpexceptions.HTTPFound)
        assert request.session.flash.call_count == 1
        assert request.session.flash.call_args[0][0].startswith(
            "You're already signed in to a different account")


@pytest.mark.usefixtures('routes_mapper')
class TestProfileController(object):

    def test_post_400s_with_no_formid(self):
        user = FakeUser()
        request = DummyRequest(post={}, authenticated_user=user)

        with pytest.raises(httpexceptions.HTTPBadRequest):
            views.ProfileController(request).post()

    def test_post_400s_with_bogus_formid(self):
        user = FakeUser()
        request = DummyRequest(post={'__formid__': 'hax0rs'},
                               authenticated_user=user)

        with pytest.raises(httpexceptions.HTTPBadRequest):
            views.ProfileController(request).post()

    def test_post_changing_email_with_valid_data_updates_email(self):
        user = FakeUser(email=None, password=None)
        request = DummyRequest(post={'__formid__': 'email'},
                               authenticated_user=user)
        controller = views.ProfileController(request)
        controller.forms['email'] = form_validating_to(
            {'email': 'amrit@example.com'})

        controller.post()

        assert user.email == 'amrit@example.com'

    def test_post_changing_email_with_valid_data_redirects(self):
        user = FakeUser(email=None, password=None)
        request = DummyRequest(post={'__formid__': 'email'},
                               authenticated_user=user)
        controller = views.ProfileController(request)
        controller.forms['email'] = form_validating_to(
            {'email': 'amrit@example.com'})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPFound)

    def test_post_changing_email_with_invalid_data_returns_form(self):
        user = FakeUser(email=None, password=None)
        request = DummyRequest(post={'__formid__': 'email'},
                               authenticated_user=user)
        controller = views.ProfileController(request)
        controller.forms['email'] = invalid_form()

        result = controller.post()

        assert 'email_form' in result

    def test_post_changing_email_with_invalid_data_does_not_update_email(self):
        user = FakeUser(email=None, password=None)
        request = DummyRequest(post={'__formid__': 'email'},
                               authenticated_user=user)
        controller = views.ProfileController(request)
        controller.forms['email'] = invalid_form()

        controller.post()

        assert user.email is None

    def test_post_changing_password_with_valid_data_updates_password(self):
        user = FakeUser(email=None, password=None)
        request = DummyRequest(post={'__formid__': 'password'},
                               authenticated_user=user)
        controller = views.ProfileController(request)
        controller.forms['password'] = form_validating_to(
            {'new_password': 'secrets!'})

        controller.post()

        assert user.password == 'secrets!'

    def test_post_changing_password_with_valid_data_redirects(self):
        user = FakeUser(email=None, password=None)
        request = DummyRequest(post={'__formid__': 'password'},
                               authenticated_user=user)
        controller = views.ProfileController(request)
        controller.forms['password'] = form_validating_to(
            {'new_password': 'secrets!'})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPFound)

    def test_post_changing_password_with_invalid_data_returns_form(self):
        user = FakeUser(email=None, password=None)
        request = DummyRequest(post={'__formid__': 'password'},
                               authenticated_user=user)
        controller = views.ProfileController(request)
        controller.forms['password'] = invalid_form()

        result = controller.post()

        assert 'password_form' in result

    def test_post_changing_password_with_invalid_data_does_not_update_password(
            self):
        user = FakeUser(email=None, password=None)
        request = DummyRequest(post={'__formid__': 'password'},
                               authenticated_user=user)
        controller = views.ProfileController(request)
        controller.forms['password'] = invalid_form()

        controller.post()

        assert user.password is None


@pytest.mark.usefixtures('authn_policy',
                         'routes_mapper',
                         'subscriptions_model')
class TestNotificationsController(object):

    def test_get_sets_subscriptions_data_in_form(self,
                                                 authn_policy,
                                                 subscriptions_model):
        request = DummyRequest()
        authn_policy.authenticated_userid.return_value = 'fiona'
        subscriptions_model.get_subscriptions_for_uri.return_value = [
            FakeSubscription('reply', True),
            FakeSubscription('foo', False),
        ]
        controller = views.NotificationsController(request)
        controller.form = form_validating_to({})

        controller.get()

        controller.form.set_appstruct.assert_called_once_with({
            'notifications': set(['reply']),
        })

    def test_post_with_invalid_data_returns_form(self, authn_policy):
        request = DummyRequest(post={})
        authn_policy.authenticated_userid.return_value = 'jerry'
        controller = views.NotificationsController(request)
        controller.form = invalid_form()

        result = controller.post()

        assert 'form' in result

    def test_post_with_valid_data_updates_subscriptions(self,
                                                        authn_policy,
                                                        subscriptions_model):
        request = DummyRequest(post={})
        authn_policy.authenticated_userid.return_value = 'fiona'
        subs = [
            FakeSubscription('reply', True),
            FakeSubscription('foo', False),
        ]
        subscriptions_model.get_subscriptions_for_uri.return_value = subs
        controller = views.NotificationsController(request)
        controller.form = form_validating_to({
            'notifications': set(['foo'])
        })

        controller.post()

        assert subs[0].active is False
        assert subs[1].active is True

    def test_post_with_valid_data_redirects(self,
                                            authn_policy,
                                            subscriptions_model):
        request = DummyRequest(post={})
        authn_policy.authenticated_userid.return_value = 'fiona'
        subscriptions_model.get_subscriptions_for_uri.return_value = []
        controller = views.NotificationsController(request)
        controller.form = form_validating_to({})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPFound)


@pytest.mark.usefixtures('models')
class TestDeveloperController(object):

    def test_get_gets_token_for_authenticated_userid(self, models):
        request = testing.DummyRequest()

        views.DeveloperController(request).get()

        models.Token.get_by_userid.assert_called_once_with(
            request.authenticated_userid)

    def test_get_returns_token(self, models):
        token = API_TOKEN_PREFIX + u'abc123'
        models.Token.get_by_userid.return_value.value = token

        data = views.DeveloperController(testing.DummyRequest()).get()

        assert data.get('token') == token

    def test_get_with_no_token(self, models):
        models.Token.get_by_userid.return_value = None

        assert views.DeveloperController(testing.DummyRequest()).get() == {}

    def test_post_gets_token_for_authenticated_userid(self, models):
        request = testing.DummyRequest()

        views.DeveloperController(request).post()

        models.Token.get_by_userid.assert_called_once_with(
            request.authenticated_userid)

    def test_post_calls_regenerate(self, models):
        """If the user already has a token it should regenerate it."""
        views.DeveloperController(testing.DummyRequest()).post()

        models.Token.get_by_userid.return_value.regenerate.assert_called_with()

    def test_post_inits_new_token_for_authenticated_userid(self, models):
        """If the user doesn't have a token yet it should generate one."""
        models.Token.get_by_userid.return_value = None
        request = testing.DummyRequest(db=mock.Mock())

        views.DeveloperController(request).post()

        models.Token.assert_called_once_with(request.authenticated_userid)

    def test_post_adds_new_token_to_db(self, models):
        """If the user doesn't have a token yet it should add one to the db."""
        models.Token.get_by_userid.return_value = None
        request = testing.DummyRequest(db=mock.Mock())

        views.DeveloperController(request).post()

        request.db.add.assert_called_once_with(models.Token.return_value)

        models.Token.assert_called_once_with(request.authenticated_userid)

    def test_post_returns_token_after_regenerating(self, models):
        """After regenerating a token it should return its new value."""
        data = views.DeveloperController(testing.DummyRequest()).post()

        assert data['token'] == models.Token.get_by_userid.return_value.value

    def test_post_returns_token_after_generating(self, models):
        """After generating a new token it should return its value."""
        models.Token.get_by_userid.return_value = None
        request = testing.DummyRequest(db=mock.Mock())

        data = views.DeveloperController(request).post()

        assert data['token'] == models.Token.return_value.value


@pytest.fixture
def pop_flash(request):
    patcher = mock.patch('h.accounts.views.session.pop_flash', autospec=True)
    func = patcher.start()
    request.addfinalizer(patcher.stop)
    return func


@pytest.fixture
def session(request):
    patcher = mock.patch('h.accounts.views.session', autospec=True)
    session = patcher.start()
    request.addfinalizer(patcher.stop)
    return session


@pytest.fixture
def subscriptions_model(request):
    patcher = mock.patch('h.models.Subscriptions', autospec=True)
    model = patcher.start()
    request.addfinalizer(patcher.stop)
    return model


@pytest.fixture
def user_model(request):
    patcher = mock.patch('h.accounts.views.User', autospec=True)
    model = patcher.start()
    request.addfinalizer(patcher.stop)
    return model


@pytest.fixture
def activation_model(request):
    patcher = mock.patch('h.accounts.views.Activation', autospec=True)
    model = patcher.start()
    request.addfinalizer(patcher.stop)
    return model


@pytest.fixture
def ActivationEvent(request):
    patcher = mock.patch('h.accounts.views.ActivationEvent', autospec=True)
    model = patcher.start()
    request.addfinalizer(patcher.stop)
    return model


@pytest.fixture
def mailer(request):
    patcher = mock.patch('h.accounts.views.mailer', autospec=True)
    module = patcher.start()
    request.addfinalizer(patcher.stop)
    return module


@pytest.fixture
def models(request):
    patcher = mock.patch('h.accounts.views.models', autospec=True)
    module = patcher.start()
    request.addfinalizer(patcher.stop)
    return module
