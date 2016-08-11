# -*- coding: utf-8 -*-
# pylint: disable=no-self-use

import mock
import pytest

import deform
from pyramid import httpexceptions

from h import accounts
from h.accounts import views

from tests.h import conftest


class FakeSubscription(object):
    def __init__(self, type_, active):
        self.type = type_
        self.active = active


class FakeUser(object):
    def __init__(self, **kwargs):
        defaults = {'activation': None, 'email': None, 'password': None}
        defaults.update(kwargs)
        for k, v in defaults.items():
            setattr(self, k, v)


class FakeSerializer(object):
    def dumps(self, obj):
        return 'faketoken'

    def loads(self, token):
        return {'username': 'foo@bar.com'}


@pytest.mark.usefixtures('routes')
class TestAuthController(object):

    def test_post_redirects_when_logged_in(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")

        with pytest.raises(httpexceptions.HTTPFound):
            views.AuthController(pyramid_request).post()

    def test_post_redirects_to_next_param_when_logged_in(self, pyramid_config, pyramid_request):
        pyramid_request.params = {'next': '/foo/bar'}
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")

        with pytest.raises(httpexceptions.HTTPFound) as e:
            views.AuthController(pyramid_request).post()

        assert e.value.location == '/foo/bar'

    def test_post_returns_form_when_validation_fails(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy(None)  # Logged out
        controller = views.AuthController(pyramid_request)
        controller.form = conftest.invalid_form()

        result = controller.post()

        assert result == {'form': 'invalid form'}

    @mock.patch('h.accounts.views.LoginEvent', autospec=True)
    def test_post_no_event_when_validation_fails(self,
                                                 loginevent,
                                                 notify,
                                                 pyramid_config,
                                                 pyramid_request):
        pyramid_config.testing_securitypolicy(None)  # Logged out
        controller = views.AuthController(pyramid_request)
        controller.form = conftest.invalid_form()

        controller.post()

        assert not loginevent.called
        assert not notify.called

    def test_post_redirects_when_validation_succeeds(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy(None)  # Logged out
        controller = views.AuthController(pyramid_request)
        controller.form = conftest.form_validating_to(
            {"user": FakeUser(username='cara')})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPFound)

    def test_post_redirects_to_next_param_when_validation_succeeds(self,
                                                                   pyramid_config,
                                                                   pyramid_request):
        pyramid_request.params = {'next': '/foo/bar'}
        pyramid_config.testing_securitypolicy(None)  # Logged out
        controller = views.AuthController(pyramid_request)
        controller.form = conftest.form_validating_to(
            {"user": FakeUser(username='cara')})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPFound)
        assert result.location == '/foo/bar'

    @mock.patch('h.accounts.views.LoginEvent', autospec=True)
    def test_post_event_when_validation_succeeds(self,
                                                 loginevent,
                                                 notify,
                                                 pyramid_config,
                                                 pyramid_request):
        pyramid_config.testing_securitypolicy(None)  # Logged out
        elephant = FakeUser(username='avocado')
        controller = views.AuthController(pyramid_request)
        controller.form = conftest.form_validating_to({"user": elephant})

        controller.post()

        loginevent.assert_called_with(pyramid_request, elephant)
        notify.assert_called_with(loginevent.return_value)

    @mock.patch('h.accounts.views.LogoutEvent', autospec=True)
    def test_logout_event(self, logoutevent, notify, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")

        views.AuthController(pyramid_request).logout()

        logoutevent.assert_called_with(pyramid_request)
        notify.assert_called_with(logoutevent.return_value)

    def test_logout_invalidates_session(self, pyramid_config, pyramid_request):
        pyramid_request.session["foo"] = "bar"
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")

        views.AuthController(pyramid_request).logout()

        assert "foo" not in pyramid_request.session

    def test_logout_redirects(self, pyramid_request):
        result = views.AuthController(pyramid_request).logout()

        assert isinstance(result, httpexceptions.HTTPFound)

    def test_logout_response_has_forget_headers(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy(forget_result={
            'x-erase-fingerprints': 'on the hob'
        })

        result = views.AuthController(pyramid_request).logout()

        assert result.headers['x-erase-fingerprints'] == 'on the hob'

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('forgot_password', '/forgot')
        pyramid_config.add_route('index', '/index')
        pyramid_config.add_route('stream', '/stream')


@pytest.mark.usefixtures('session')
class TestAjaxAuthController(object):

    def test_login_returns_status_okay_when_validation_succeeds(self, pyramid_request):
        pyramid_request.json_body = {}
        controller = views.AjaxAuthController(pyramid_request)
        controller.form = conftest.form_validating_to(
            {'user': FakeUser(username='bob')})

        result = controller.login()

        assert result['status'] == 'okay'

    def test_login_raises_JSONError_on_non_json_body(self, pyramid_request):
        type(pyramid_request).json_body = {}
        with mock.patch.object(type(pyramid_request),
                               'json_body',
                               new_callable=mock.PropertyMock) as json_body:
            json_body.side_effect = ValueError()

            controller = views.AjaxAuthController(pyramid_request)

            with pytest.raises(accounts.JSONError) as exc_info:
                controller.login()
                assert exc_info.value.message.startswith(
                    'Could not parse request body as JSON: ')

    def test_login_raises_JSONError_on_non_object_json(self, pyramid_request):
        pyramid_request.authenticated_user = mock.Mock(groups=[])
        pyramid_request.json_body = 'foo'

        controller = views.AjaxAuthController(pyramid_request)
        expected_message = 'Request JSON body must have a top-level object'

        with pytest.raises(accounts.JSONError) as exc_info:
            controller.login()

        assert exc_info.value.message == expected_message

    def test_login_converts_non_string_usernames_to_strings(self, pyramid_csrf_request):
        for input_, expected_output in ((None, ''),
                                        (23, '23'),
                                        (True, 'True')):
            pyramid_csrf_request.json_body = {'username': input_,
                                              'password': 'pass'}
            controller = views.AjaxAuthController(pyramid_csrf_request)
            controller.form.validate = mock.Mock(
                return_value={'user': mock.Mock()})

            controller.login()

            assert controller.form.validate.called
            pstruct = controller.form.validate.call_args[0][0]
            assert sorted(pstruct) == sorted([('username', expected_output),
                                              ('password', 'pass')])

    def test_login_converts_non_string_passwords_to_strings(self, pyramid_csrf_request):
        for input_, expected_output in ((None, ''),
                                        (23, '23'),
                                        (True, 'True')):
            pyramid_csrf_request.json_body = {'username': 'user',
                                              'password': input_}
            controller = views.AjaxAuthController(pyramid_csrf_request)
            controller.form.validate = mock.Mock(
                return_value={'user': mock.Mock()})

            controller.login()

            assert controller.form.validate.called
            pstruct = controller.form.validate.call_args[0][0]
            assert sorted(pstruct) == sorted([('username', 'user'),
                                              ('password', expected_output)])

    def test_login_raises_ValidationFailure_on_ValidationFailure(self, pyramid_request):
        pyramid_request.json_body = {}
        controller = views.AjaxAuthController(pyramid_request)
        controller.form = conftest.invalid_form({'password': 'too short'})

        with pytest.raises(deform.ValidationFailure) as exc_info:
            controller.login()

        assert exc_info.value.error.asdict() == {'password': 'too short'}

    def test_logout_returns_status_okay(self, pyramid_request):
        result = views.AjaxAuthController(pyramid_request).logout()

        assert result['status'] == 'okay'


@pytest.mark.usefixtures('activation_model',
                         'mailer',
                         'routes')
class TestForgotPasswordController(object):

    def test_post_returns_form_when_validation_fails(self, pyramid_request):
        controller = views.ForgotPasswordController(pyramid_request)
        controller.form = conftest.invalid_form()

        result = controller.post()

        assert result == {'form': 'invalid form'}

    def test_post_creates_no_activations_when_validation_fails(self,
                                                               activation_model,
                                                               pyramid_request):
        controller = views.ForgotPasswordController(pyramid_request)
        controller.form = conftest.invalid_form()

        controller.post()

        assert activation_model.call_count == 0

    @mock.patch('h.accounts.views.account_reset_link')
    def test_post_generates_reset_link(self, reset_link, pyramid_request):
        pyramid_request.registry.password_reset_serializer = FakeSerializer()
        user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
        controller = views.ForgotPasswordController(pyramid_request)
        controller.form = conftest.form_validating_to({"user": user})

        controller.post()

        reset_link.assert_called_with(pyramid_request, "faketoken")

    @mock.patch('h.accounts.views.account_reset_email')
    @mock.patch('h.accounts.views.account_reset_link')
    def test_post_generates_mail(self,
                                 reset_link,
                                 reset_mail,
                                 activation_model,
                                 pyramid_request):
        pyramid_request.registry.password_reset_serializer = FakeSerializer()
        user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
        controller = views.ForgotPasswordController(pyramid_request)
        controller.form = conftest.form_validating_to({"user": user})
        reset_link.return_value = "http://example.com"
        reset_mail.return_value = {
            'recipients': [],
            'subject': '',
            'body': ''
        }

        controller.post()

        reset_mail.assert_called_with(user, "faketoken", "http://example.com")

    @mock.patch('h.accounts.views.account_reset_email')
    def test_post_sends_mail(self, reset_mail, mailer, pyramid_request):
        pyramid_request.registry.password_reset_serializer = FakeSerializer()
        user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
        controller = views.ForgotPasswordController(pyramid_request)
        controller.form = conftest.form_validating_to({"user": user})
        reset_mail.return_value = {
            'recipients': ['giraffe@thezoo.org'],
            'subject': 'subject',
            'body': 'body'
        }

        controller.post()

        mailer.send.delay.assert_called_once_with(recipients=['giraffe@thezoo.org'],
                                                  subject='subject',
                                                  body='body')

    def test_post_redirects_on_success(self, pyramid_request):
        pyramid_request.registry.password_reset_serializer = FakeSerializer()
        user = FakeUser(username='giraffe', email='giraffe@thezoo.org')
        controller = views.ForgotPasswordController(pyramid_request)
        controller.form = conftest.form_validating_to({"user": user})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPRedirection)

    def test_get_redirects_when_logged_in(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")

        with pytest.raises(httpexceptions.HTTPFound):
            views.ForgotPasswordController(pyramid_request).get()

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('index', '/index')
        pyramid_config.add_route('account_reset', '/account/reset')
        pyramid_config.add_route('account_reset_with_code', '/account/reset-with-code')


@pytest.mark.usefixtures('routes')
class TestResetController(object):

    def test_post_returns_form_when_validation_fails(self, pyramid_request):
        controller = views.ResetController(pyramid_request)
        controller.form = conftest.invalid_form()

        result = controller.post()

        assert result == {'form': 'invalid form'}

    def test_post_sets_user_password_from_form(self, pyramid_request):
        elephant = FakeUser(password='password1')
        controller = views.ResetController(pyramid_request)
        controller.form = conftest.form_validating_to({'user': elephant,
                                                       'password': 's3cure!'})

        controller.post()

        assert elephant.password == 's3cure!'

    @mock.patch('h.accounts.views.PasswordResetEvent', autospec=True)
    def test_post_emits_event(self, event, notify, pyramid_request):
        user = FakeUser(password='password1')
        controller = views.ResetController(pyramid_request)
        controller.form = conftest.form_validating_to({'user': user,
                                                       'password': 's3cure!'})

        controller.post()

        event.assert_called_with(pyramid_request, user)
        notify.assert_called_with(event.return_value)

    def test_post_redirects_on_success(self, pyramid_request):
        user = FakeUser(password='password1')
        controller = views.ResetController(pyramid_request)
        controller.form = conftest.form_validating_to({'user': user,
                                                       'password': 's3cure!'})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPRedirection)

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('index', '/index')
        pyramid_config.add_route('login', '/login')
        pyramid_config.add_route('account_reset', '/reset')
        pyramid_config.add_route('account_reset_with_code', '/reset-with-code')


@pytest.mark.usefixtures('activation_model',
                         'pyramid_config',
                         'mailer',
                         'notify',
                         'routes',
                         'user_model')
class TestSignupController(object):

    def test_post_returns_errors_when_validation_fails(self, pyramid_request):
        controller = views.SignupController(pyramid_request)
        controller.form = conftest.invalid_form()

        result = controller.post()

        assert result == {"form": "invalid form"}

    def test_post_creates_user_from_form_data(self, pyramid_request, user_model):
        controller = views.SignupController(pyramid_request)
        controller.form = conftest.form_validating_to({
            "username": "bob",
            "email": "bob@example.com",
            "password": "s3crets",
            "random_other_field": "something else",
        })

        controller.post()

        user_model.assert_called_with(username="bob",
                                      email="bob@example.com",
                                      password="s3crets")

    def test_post_adds_new_user_to_session(self, pyramid_request, user_model):
        controller = views.SignupController(pyramid_request)
        controller.form = conftest.form_validating_to({
            "username": "bob",
            "email": "bob@example.com",
            "password": "s3crets",
        })

        controller.post()

        assert user_model.return_value in pyramid_request.db.added

    def test_post_creates_new_activation(self, activation_model, pyramid_request, user_model):
        controller = views.SignupController(pyramid_request)
        controller.form = conftest.form_validating_to({
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
                                                       pyramid_request,
                                                       user_model):
        controller = views.SignupController(pyramid_request)
        controller.form = conftest.form_validating_to({
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

        activation_email.assert_called_once_with(pyramid_request, new_user)

    @mock.patch('h.accounts.views.activation_email')
    def test_post_sends_email(self, activation_email, mailer, pyramid_request):
        controller = views.SignupController(pyramid_request)
        controller.form = conftest.form_validating_to({
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

        mailer.send.delay.assert_called_once_with(recipients=['bob@example.com'],
                                                  subject='subject',
                                                  body='body')

    @mock.patch('h.accounts.views.RegistrationEvent')
    def test_post_no_event_when_validation_fails(self, event, notify, pyramid_request):
        controller = views.SignupController(pyramid_request)
        controller.form = conftest.invalid_form()

        controller.post()

        assert not event.called
        assert not notify.called

    @mock.patch('h.accounts.views.RegistrationEvent')
    def test_post_event_when_validation_succeeds(self,
                                                 event,
                                                 notify,
                                                 pyramid_request,
                                                 user_model):
        controller = views.SignupController(pyramid_request)
        controller.form = conftest.form_validating_to({
            "username": "bob",
            "email": "bob@example.com",
            "password": "s3crets",
        })
        new_user = user_model.return_value

        controller.post()

        event.assert_called_with(pyramid_request, new_user)
        notify.assert_called_with(event.return_value)

    def test_post_event_redirects_on_success(self, pyramid_request):
        controller = views.SignupController(pyramid_request)
        controller.form = conftest.form_validating_to({
            "username": "bob",
            "email": "bob@example.com",
            "password": "s3crets",
        })

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPRedirection)

    def test_get_redirects_when_logged_in(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")
        controller = views.SignupController(pyramid_request)

        with pytest.raises(httpexceptions.HTTPRedirection):
            controller.get()

    @pytest.fixture
    def pyramid_request(self, pyramid_request, fake_db_session):
        # Override the database session with a fake session implementation.
        # FIXME: don't mock models...
        pyramid_request.db = fake_db_session
        return pyramid_request

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('activate', '/activate')
        pyramid_config.add_route('index', '/index')
        pyramid_config.add_route('stream', '/stream')


@pytest.mark.usefixtures('ActivationEvent',
                         'activation_model',
                         'notify',
                         'routes',
                         'user_model')
class TestActivateController(object):

    def test_get_when_not_logged_in_404s_if_id_not_int(self, pyramid_request):
        pyramid_request.matchdict = {'id': 'abc',  # Not an int.
                                     'code': 'abc456'}

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(pyramid_request).get_when_not_logged_in()

    def test_get_when_not_logged_in_looks_up_activation_by_code(
            self,
            activation_model,
            pyramid_request,
            user_model):
        pyramid_request.matchdict = {'id': '123', 'code': 'abc456'}
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()

        activation_model.get_by_code.assert_called_with(pyramid_request.db, 'abc456')

    def test_get_when_not_logged_in_redirects_if_activation_not_found(
            self,
            activation_model,
            pyramid_request):
        """

        If the activation code doesn't match any activation then we redirect to
        the front page and flash a message suggesting that they may already be
        activated and can log in.

        This happens if a user clicks on an activation link from an email after
        they've already been activated, for example.

        (This also happens if users visit a bogus activation URL, but we're
        happy to do this same redirect in that edge case.)

        """
        pyramid_request.matchdict = {'id': '123', 'code': 'abc456'}
        activation_model.get_by_code.return_value = None

        result = views.ActivateController(pyramid_request).get_when_not_logged_in()
        error_flash = pyramid_request.session.peek_flash('error')

        assert isinstance(result, httpexceptions.HTTPFound)
        assert error_flash
        assert error_flash[0].startswith("We didn't recognize that activation link.")

    def test_get_when_not_logged_in_looks_up_user_by_activation(
            self,
            activation_model,
            pyramid_request,
            user_model):
        pyramid_request.matchdict = {'id': '123', 'code': 'abc456'}
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()

        user_model.get_by_activation.assert_called_once_with(
            pyramid_request.db,
            activation_model.get_by_code.return_value)

    def test_get_when_not_logged_in_404s_if_user_not_found(self, pyramid_request, user_model):
        pyramid_request.matchdict = {'id': '123', 'code': 'abc456'}
        user_model.get_by_activation.return_value = None

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(pyramid_request).get_when_not_logged_in()

    def test_get_when_not_logged_in_404s_if_user_id_does_not_match_hash(
            self,
            pyramid_request,
            user_model):
        """

        We don't want to let a user with a valid hash activate a different
        user's account!

        """
        pyramid_request.matchdict = {'id': '123', 'code': 'abc456'}
        user_model.get_by_activation.return_value.id = 2  # Not the same id.

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(pyramid_request).get_when_not_logged_in()

    def test_get_when_not_logged_in_successful_activates_user(
            self,
            pyramid_request,
            user_model):
        pyramid_request.matchdict = {'id': '123', 'code': 'abc456'}
        pyramid_request.db.delete = mock.create_autospec(pyramid_request.db.delete,
                                                         return_value=None)
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()

        user_model.get_by_activation.return_value.activate.assert_called_once_with()

    def test_get_when_not_logged_in_successful_flashes_message(self,
                                                               pyramid_request,
                                                               user_model):
        pyramid_request.matchdict = {'id': '123', 'code': 'abc456'}
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()
        success_flash = pyramid_request.session.peek_flash('success')

        assert success_flash
        assert success_flash[0].startswith("Your account has been activated")

    def test_get_when_not_logged_in_successful_creates_ActivationEvent(
            self,
            pyramid_request,
            user_model,
            ActivationEvent):
        pyramid_request.matchdict = {'id': '123', 'code': 'abc456'}
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()

        ActivationEvent.assert_called_once_with(
            pyramid_request, user_model.get_by_activation.return_value)

    def test_get_when_not_logged_in_successful_notifies(self,
                                                        notify,
                                                        pyramid_request,
                                                        user_model,
                                                        ActivationEvent):
        pyramid_request.matchdict = {'id': '123', 'code': 'abc456'}
        user_model.get_by_activation.return_value.id = 123

        views.ActivateController(pyramid_request).get_when_not_logged_in()

        notify.assert_called_once_with(ActivationEvent.return_value)

    def test_get_when_logged_in_already_logged_in_when_id_not_an_int(self, pyramid_request):
        pyramid_request.authenticated_user = mock.Mock(id=123, spec=['id'])
        pyramid_request.matchdict = {'id': 'abc',  # Not an int.
                                     'code': 'abc456'}

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.ActivateController(pyramid_request).get_when_logged_in()

    def test_get_when_logged_in_already_logged_in_to_same_account(self, pyramid_request):
        pyramid_request.authenticated_user = mock.Mock(id=123, spec=['id'])
        pyramid_request.matchdict = {'id': '123',
                                     'code': 'abc456'}

        result = views.ActivateController(pyramid_request).get_when_logged_in()
        success_flash = pyramid_request.session.peek_flash('success')

        assert isinstance(result, httpexceptions.HTTPFound)
        assert success_flash
        assert success_flash[0].startswith(
            "Your account has been activated and you're now logged in")

    def test_get_when_logged_in_already_logged_in_to_different_account(self, pyramid_request):
        pyramid_request.authenticated_user = mock.Mock(id=124, spec=['id'])
        pyramid_request.matchdict = {'id': '123',
                                     'code': 'abc456'}

        result = views.ActivateController(pyramid_request).get_when_logged_in()
        error_flash = pyramid_request.session.peek_flash('error')

        assert isinstance(result, httpexceptions.HTTPFound)
        assert error_flash
        assert error_flash[0].startswith(
            "You're already logged in to a different account")

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('index', '/index')
        pyramid_config.add_route('login', '/login')
        pyramid_config.add_route('logout', '/logout')


@pytest.mark.usefixtures('routes')
class TestAccountController(object):

    def test_post_email_form_with_valid_data_changes_email(self,
                                                           pyramid_request):
        controller = views.AccountController(pyramid_request)
        controller.forms['email'] = conftest.form_validating_to({
            'email': 'new_email_address'})

        controller.post_email_form()

        assert pyramid_request.authenticated_user.email == 'new_email_address'

    def test_post_email_form_with_invalid_data_does_not_change_email(
            self, invalid_form, pyramid_request):
        controller = views.AccountController(pyramid_request)
        controller.forms['email'] = invalid_form
        original_email = pyramid_request.authenticated_user.email

        controller.post_email_form()

        assert pyramid_request.authenticated_user.email == original_email

    def test_post_email_form_with_invalid_data_returns_template_data(
            self, invalid_form, pyramid_request):
        controller = views.AccountController(pyramid_request)
        controller.forms['email'] = invalid_form

        result = controller.post_email_form()

        assert result == {
            'email': pyramid_request.authenticated_user.email,
            'email_form': controller.forms['email'],
            'password_form': controller.forms['password'],
        }

    def test_post_password_form_with_valid_data_changes_password(
            self, pyramid_request):
        controller = views.AccountController(pyramid_request)
        controller.forms['password'] = conftest.form_validating_to({
            'new_password': 'my_new_password'})

        controller.post_password_form()

        assert pyramid_request.authenticated_user.password == 'my_new_password'

    def test_post_password_form_with_invalid_data_does_not_change_password(
            self, invalid_form, pyramid_request):
        controller = views.AccountController(pyramid_request)
        controller.forms['password'] = invalid_form
        original_password = pyramid_request.authenticated_user.password

        controller.post_password_form()

        assert pyramid_request.authenticated_user.password == original_password

    def test_post_password_form_with_invalid_data_returns_template_data(
            self, invalid_form, pyramid_request):
        controller = views.AccountController(pyramid_request)
        controller.forms['password'] = invalid_form

        result = controller.post_password_form()

        assert result == {
            'email': pyramid_request.authenticated_user.email,
            'email_form': controller.forms['email'],
            'password_form': controller.forms['password'],
        }

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.POST = {}
        pyramid_request.authenticated_user = user
        return pyramid_request

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('account', '/my/account')

    @pytest.fixture
    def user(self):
        return FakeUser()


@pytest.mark.usefixtures('pyramid_config',
                         'routes',
                         'subscriptions_model')
class TestNotificationsController(object):

    def test_get_sets_subscriptions_data_in_form(self,
                                                 pyramid_config,
                                                 pyramid_request,
                                                 subscriptions_model):
        pyramid_config.testing_securitypolicy('fiona')
        subscriptions_model.get_subscriptions_for_uri.return_value = [
            FakeSubscription('reply', True),
            FakeSubscription('foo', False),
        ]
        controller = views.NotificationsController(pyramid_request)
        controller.form = conftest.form_validating_to({})

        controller.get()

        controller.form.set_appstruct.assert_called_once_with({
            'notifications': set(['reply']),
        })

    def test_post_with_invalid_data_returns_form(self, pyramid_config, pyramid_request):
        pyramid_request.POST = {}
        pyramid_config.testing_securitypolicy('jerry')
        controller = views.NotificationsController(pyramid_request)
        controller.form = conftest.invalid_form()

        result = controller.post()

        assert 'form' in result

    def test_post_with_valid_data_updates_subscriptions(self,
                                                        pyramid_config,
                                                        pyramid_request,
                                                        subscriptions_model):
        pyramid_request.POST = {}
        pyramid_config.testing_securitypolicy('fiona')
        subs = [
            FakeSubscription('reply', True),
            FakeSubscription('foo', False),
        ]
        subscriptions_model.get_subscriptions_for_uri.return_value = subs
        controller = views.NotificationsController(pyramid_request)
        controller.form = conftest.form_validating_to({
            'notifications': set(['foo'])
        })

        controller.post()

        assert subs[0].active is False
        assert subs[1].active is True

    def test_post_with_valid_data_redirects(self,
                                            pyramid_config,
                                            pyramid_request,
                                            subscriptions_model):
        pyramid_request.POST = {}
        pyramid_config.testing_securitypolicy('fiona')
        subscriptions_model.get_subscriptions_for_uri.return_value = []
        controller = views.NotificationsController(pyramid_request)
        controller.form = conftest.form_validating_to({})

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPFound)

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('account_notifications', '/p/notifications')


@pytest.mark.usefixtures('models')
class TestDeveloperController(object):

    def test_get_gets_token_for_authenticated_userid(self, models, pyramid_request):
        views.DeveloperController(pyramid_request).get()

        models.Token.get_by_userid.assert_called_once_with(
            pyramid_request.db,
            pyramid_request.authenticated_userid)

    def test_get_returns_token(self, models, pyramid_request):
        models.Token.get_by_userid.return_value.value = u'abc123'

        data = views.DeveloperController(pyramid_request).get()

        assert data.get('token') == u'abc123'

    def test_get_with_no_token(self, models, pyramid_request):
        models.Token.get_by_userid.return_value = None

        result = views.DeveloperController(pyramid_request).get()

        assert result == {}

    def test_post_gets_token_for_authenticated_userid(self, models, pyramid_request):
        views.DeveloperController(pyramid_request).post()

        models.Token.get_by_userid.assert_called_once_with(
            pyramid_request.db,
            pyramid_request.authenticated_userid)

    def test_post_calls_regenerate(self, models, pyramid_request):
        """If the user already has a token it should regenerate it."""
        views.DeveloperController(pyramid_request).post()

        models.Token.get_by_userid.return_value.regenerate.assert_called_with()

    def test_post_inits_new_token_for_authenticated_userid(self, models, pyramid_request):
        """If the user doesn't have a token yet it should generate one."""
        models.Token.get_by_userid.return_value = None

        views.DeveloperController(pyramid_request).post()

        models.Token.assert_called_once_with(pyramid_request.authenticated_userid)

    def test_post_adds_new_token_to_db(self, models, pyramid_request):
        """If the user doesn't have a token yet it should add one to the db."""
        models.Token.get_by_userid.return_value = None

        views.DeveloperController(pyramid_request).post()

        assert models.Token.return_value in pyramid_request.db.added

        models.Token.assert_called_once_with(pyramid_request.authenticated_userid)

    def test_post_returns_token_after_regenerating(self, models, pyramid_request):
        """After regenerating a token it should return its new value."""
        data = views.DeveloperController(pyramid_request).post()

        assert data['token'] == models.Token.get_by_userid.return_value.value

    def test_post_returns_token_after_generating(self, models, pyramid_request):
        """After generating a new token it should return its value."""
        models.Token.get_by_userid.return_value = None

        data = views.DeveloperController(pyramid_request).post()

        assert data['token'] == models.Token.return_value.value

    @pytest.fixture
    def pyramid_request(self, pyramid_request, fake_db_session):
        # Override the database session with a fake session implementation.
        # FIXME: don't mock models...
        pyramid_request.db = fake_db_session
        return pyramid_request


@pytest.fixture
def session(patch):
    return patch('h.accounts.views.session')


@pytest.fixture
def subscriptions_model(patch):
    return patch('h.models.Subscriptions')


@pytest.fixture
def user_model(patch):
    return patch('h.accounts.views.User')


@pytest.fixture
def activation_model(patch):
    return patch('h.accounts.views.Activation')


@pytest.fixture
def ActivationEvent(patch):
    return patch('h.accounts.views.ActivationEvent')


@pytest.fixture
def mailer(patch):
    return patch('h.accounts.views.mailer')


@pytest.fixture
def models(patch):
    return patch('h.accounts.views.models')
