# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from mock import Mock

from h.services.user_signup import UserSignupService
from h.exceptions import ClientUnauthorized
from h.views.api_users import create
from h.schemas import ValidationError


@pytest.mark.usefixtures('auth_client',
                         'basic_auth_creds',
                         'user_signup_service')
class TestCreate(object):

    @pytest.mark.usefixtures('valid_auth')
    def test_returns_user_object(self,
                                 factories,
                                 pyramid_request,
                                 user_signup_service,
                                 valid_payload):
        pyramid_request.json_body = valid_payload
        user_signup_service.signup.return_value = factories.User.build(**valid_payload)

        result = create(pyramid_request)

        assert result == {
            'userid': 'acct:jeremy@weylandindustries.com',
            'username': 'jeremy',
            'email': 'jeremy@weylandtech.com',
            'authority': 'weylandindustries.com',
        }

    @pytest.mark.usefixtures('valid_auth')
    def test_signs_up_user(self,
                           factories,
                           pyramid_request,
                           user_signup_service,
                           valid_payload):
        pyramid_request.json_body = valid_payload
        user_signup_service.signup.return_value = factories.User.build(**valid_payload)

        create(pyramid_request)

        user_signup_service.signup.assert_called_once_with(
            require_activation=False,
            authority='weylandindustries.com',
            username='jeremy',
            email='jeremy@weylandtech.com')

    def test_raises_when_no_creds(self, pyramid_request, valid_payload):
        pyramid_request.json_body = valid_payload

        with pytest.raises(ClientUnauthorized):
            create(pyramid_request)

    def test_raises_when_malformed_client_id(self,
                                             basic_auth_creds,
                                             pyramid_request,
                                             valid_payload):
        basic_auth_creds.return_value = ('foobar', 'somerandomsecret')
        pyramid_request.json_body = valid_payload

        with pytest.raises(ClientUnauthorized):
            create(pyramid_request)

    def test_raises_when_no_client(self,
                                   basic_auth_creds,
                                   pyramid_request,
                                   valid_payload):
        basic_auth_creds.return_value = ('C69BA868-5089-4EE4-ABB6-63A1C38C395B',
                                         'somerandomsecret')
        pyramid_request.json_body = valid_payload

        with pytest.raises(ClientUnauthorized):
            create(pyramid_request)

    def test_raises_when_client_secret_invalid(self,
                                               auth_client,
                                               basic_auth_creds,
                                               pyramid_request,
                                               valid_payload):
        basic_auth_creds.return_value = (auth_client.id, 'incorrectsecret')
        pyramid_request.json_body = valid_payload

        with pytest.raises(ClientUnauthorized):
            create(pyramid_request)

    def test_raises_for_public_client(self, factories, basic_auth_creds, pyramid_request, valid_payload):
        auth_client = factories.AuthClient(authority='weylandindustries.com')
        basic_auth_creds.return_value = (auth_client.id, '')
        pyramid_request.json_body = valid_payload

        with pytest.raises(ClientUnauthorized):
            create(pyramid_request)

    @pytest.mark.usefixtures('valid_auth')
    def test_it_validates_the_input(self, pyramid_request, valid_payload, schemas):
        create_schema = schemas.CreateUserAPISchema.return_value
        create_schema.validate.return_value = valid_payload
        pyramid_request.json_body = valid_payload

        create(pyramid_request)

        create_schema.validate.assert_called_once_with(valid_payload)

    @pytest.mark.usefixtures('valid_auth')
    def test_raises_when_schema_validation_fails(self, pyramid_request, valid_payload, schemas):
        create_schema = schemas.CreateUserAPISchema.return_value
        create_schema.validate.side_effect = ValidationError('validation failed')

        pyramid_request.json_body = valid_payload

        with pytest.raises(ValidationError):
            create(pyramid_request)

    @pytest.mark.usefixtures('valid_auth')
    def test_raises_when_authority_doesnt_match(self, pyramid_request, valid_payload, auth_client):
        payload = valid_payload
        payload['authority'] = 'foo-%s' % auth_client.authority
        pyramid_request.json_body = payload

        with pytest.raises(ValidationError) as exc:
            create(pyramid_request)

        assert "'authority' does not match authenticated client" in str(exc.value)

    @pytest.mark.usefixtures('valid_auth')
    def test_raises_when_username_taken(self,
                                        pyramid_request,
                                        valid_payload,
                                        db_session,
                                        factories,
                                        auth_client):
        existing_user = factories.User(authority=auth_client.authority)
        db_session.flush()

        payload = valid_payload
        payload['username'] = existing_user.username
        pyramid_request.json_body = payload

        with pytest.raises(ValidationError) as exc:
            create(pyramid_request)

        assert ('username %s already exists' % existing_user.username) in str(exc.value)

    @pytest.mark.usefixtures('valid_auth')
    def test_raises_when_email_taken(self,
                                     pyramid_request,
                                     valid_payload,
                                     db_session,
                                     factories,
                                     auth_client):
        existing_user = factories.User(authority=auth_client.authority)
        db_session.flush()

        payload = valid_payload
        payload['email'] = existing_user.email
        pyramid_request.json_body = payload

        with pytest.raises(ValidationError) as exc:
            create(pyramid_request)

        assert ('email address %s already exists' % existing_user.email) in str(exc.value)

    @pytest.mark.usefixtures('valid_auth')
    def test_combines_unique_username_email_errors(self,
                                                   pyramid_request,
                                                   valid_payload,
                                                   db_session,
                                                   factories,
                                                   auth_client):
        existing_user = factories.User(authority=auth_client.authority)
        db_session.flush()

        payload = valid_payload
        payload['email'] = existing_user.email
        payload['username'] = existing_user.username
        pyramid_request.json_body = payload

        with pytest.raises(ValidationError) as exc:
            create(pyramid_request)

        assert ('email address %s already exists' % existing_user.email) in str(exc.value)
        assert ('username %s already exists' % existing_user.username) in str(exc.value)

    @pytest.fixture
    def schemas(self, patch):
        return patch('h.views.api_users.schemas')


@pytest.fixture
def auth_client(factories):
    return factories.ConfidentialAuthClient(authority='weylandindustries.com')


@pytest.fixture
def basic_auth_creds(patch):
    basic_auth_creds = patch('h.views.api_users.basic_auth_creds')
    basic_auth_creds.return_value = None
    return basic_auth_creds


@pytest.fixture
def valid_auth(basic_auth_creds, auth_client):
    basic_auth_creds.return_value = (auth_client.id, auth_client.secret)


@pytest.fixture
def user_signup_service(db_session, factories, pyramid_config):
    service = Mock(spec_set=UserSignupService(default_authority='example.com',
                                              mailer=None,
                                              session=None,
                                              password_service=None,
                                              signup_email=None,
                                              stats=None))
    pyramid_config.register_service(service, name='user_signup')
    return service


@pytest.fixture
def valid_payload():
    return {
        'authority': 'weylandindustries.com',
        'email': 'jeremy@weylandtech.com',
        'username': 'jeremy',
    }
