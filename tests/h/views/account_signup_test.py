# -*- coding: utf-8 -*-
# pylint: disable=no-self-use

from __future__ import unicode_literals
import mock
import pytest

from pyramid import httpexceptions

from h.services.user_signup import UserSignupService
from h.views import account_signup as views


@pytest.mark.usefixtures('pyramid_config',
                         'routes',
                         'user_signup_service')
class TestSignupController(object):

    def test_post_returns_errors_when_validation_fails(self,
                                                       invalid_form,
                                                       pyramid_request):
        controller = views.SignupController(pyramid_request)
        controller.form = invalid_form()

        result = controller.post()

        # invalid_form renders as "invalid form"
        assert result == {"form": "invalid form"}

    def test_post_creates_user_from_form_data(self,
                                              form_validating_to,
                                              pyramid_request,
                                              user_signup_service,
                                              datetime):
        controller = views.SignupController(pyramid_request)
        controller.form = form_validating_to({
            "username": "bob",
            "email": "bob@example.com",
            "password": "s3crets",
            "random_other_field": "something else",
        })

        controller.post()

        user_signup_service.signup.assert_called_with(username="bob",
                                                      email="bob@example.com",
                                                      password="s3crets",
                                                      privacy_accepted=datetime.datetime.utcnow.return_value)

    def test_post_does_not_create_user_when_validation_fails(self,
                                                             invalid_form,
                                                             pyramid_request,
                                                             user_signup_service):
        controller = views.SignupController(pyramid_request)
        controller.form = invalid_form()

        controller.post()

        assert not user_signup_service.signup.called

    def test_post_redirects_on_success(self,
                                       form_validating_to,
                                       pyramid_request):
        controller = views.SignupController(pyramid_request)
        controller.form = form_validating_to({
            "username": "bob",
            "email": "bob@example.com",
            "password": "s3crets",
        })

        result = controller.post()

        assert isinstance(result, httpexceptions.HTTPRedirection)

    def test_get_renders_form_when_not_logged_in(self, pyramid_request):
        controller = views.SignupController(pyramid_request)
        controller.form.render = mock.Mock()

        assert controller.get() == {'form': controller.form.render.return_value}

    def test_get_redirects_when_logged_in(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy("acct:jane@doe.org")
        pyramid_request.user = mock.Mock(username='janedoe')
        controller = views.SignupController(pyramid_request)

        with pytest.raises(httpexceptions.HTTPRedirection):
            controller.get()


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('activity.user_search', '/users/{username}')
    pyramid_config.add_route('index', '/index')


@pytest.fixture
def user_signup_service(pyramid_config):
    service = mock.create_autospec(UserSignupService, spec_set=True, instance=True)
    pyramid_config.register_service(service, name='user_signup')
    return service


@pytest.fixture
def datetime(patch):
    return patch('h.views.account_signup.datetime')
