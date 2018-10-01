# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from mock import Mock

import colander

from pyramid.exceptions import BadCSRFToken

from h.schemas.forms.accounts.change_email import ChangeEmailSchema
from h.services.user_password import UserPasswordService


@pytest.mark.usefixtures('unique_email', 'user_password_service')
class TestEmailChangeSchema(object):

    def test_it_returns_the_new_email_when_valid(self, schema):
        appstruct = schema.deserialize({
            'email': 'foo@bar.com',
            'password': 'flibble',
        })

        assert appstruct['email'] == 'foo@bar.com'

    def test_it_proxies_email_validation_to_validator(self, pyramid_request, unique_email):
        schema = ChangeEmailSchema().bind(request=pyramid_request)

        schema.deserialize({
            'email': 'foo@bar.com',
            'password': 'flibble',
        })

        assert unique_email.call_count == 1

    def test_it_is_invalid_if_csrf_token_missing(self,
                                                 pyramid_request,
                                                 schema):
        del pyramid_request.headers['X-CSRF-Token']

        with pytest.raises(BadCSRFToken):
            schema.deserialize({
                'email': 'foo@bar.com',
                'password': 'flibble',
            })

    def test_it_is_invalid_if_csrf_token_wrong(self, pyramid_request, schema):
        pyramid_request.headers['X-CSRF-Token'] = 'WRONG'

        with pytest.raises(BadCSRFToken):
            schema.deserialize({
                'email': 'foo@bar.com',
                'password': 'flibble',
            })

    def test_it_is_invalid_if_password_wrong(self, schema, user_password_service):
        user_password_service.check_password.return_value = False

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({
                'email': 'foo@bar.com',
                'password': 'WRONG'
            })

        assert exc.value.asdict() == {'password': 'Wrong password.'}


@pytest.fixture
def pyramid_request(pyramid_csrf_request, user):
    pyramid_csrf_request.user = user
    return pyramid_csrf_request


@pytest.fixture
def schema(pyramid_request):
    return ChangeEmailSchema().bind(request=pyramid_request)


@pytest.fixture
def user(factories):
    return factories.User.build()


@pytest.fixture
def unique_email(patch):
    return patch('h.schemas.forms.accounts.change_email.unique_email')


@pytest.fixture
def user_password_service(pyramid_config):
    service = Mock(spec_set=UserPasswordService())
    service.check_password.return_value = True
    pyramid_config.register_service(service, name='user_password')
    return service
