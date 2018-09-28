# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.exceptions import PayloadError, ConflictError
from h.models.auth_client import GrantType
from h.schemas import ValidationError
from h.services.user_signup import UserSignupService
from h.services.user_unique import UserUniqueService, DuplicateUserError
from h.views.api.users import create, update


@pytest.mark.usefixtures('client_authority',
                         'user_signup_service',
                         'user_unique_svc')
class TestCreate(object):
    def test_signs_up_user(self,
                           pyramid_request,
                           user_signup_service,
                           valid_payload):
        pyramid_request.json_body = valid_payload

        create(pyramid_request)

        user_signup_service.signup.assert_called_once_with(
            require_activation=False,
            authority='weylandindustries.com',
            username='jeremy',
            email='jeremy@weylandtech.com',
            display_name='Jeremy Weyland',
            identities=[{'provider': 'provider_a', 'provider_unique_id': 'abc123'}])

    def test_it_presents_user(self, pyramid_request, valid_payload, user, presenter):
        pyramid_request.json_body = valid_payload
        create(pyramid_request)

        presenter.assert_called_once_with(user)

    def test_it_returns_presented_user(self, pyramid_request, valid_payload, presenter):
        pyramid_request.json_body = valid_payload
        result = create(pyramid_request)

        assert result == presenter.return_value.asdict()

    def test_it_validates_the_input(self, pyramid_request, valid_payload, CreateUserAPISchema):
        create_schema = CreateUserAPISchema.return_value
        create_schema.validate.return_value = valid_payload
        pyramid_request.json_body = valid_payload

        create(pyramid_request)

        create_schema.validate.assert_called_once_with(valid_payload)

    def test_raises_when_schema_validation_fails(self, pyramid_request, valid_payload, CreateUserAPISchema):
        create_schema = CreateUserAPISchema.return_value
        create_schema.validate.side_effect = ValidationError('validation failed')

        pyramid_request.json_body = valid_payload

        with pytest.raises(ValidationError):
            create(pyramid_request)

    def test_raises_ValidationError_when_authority_mismatch(self, pyramid_request, valid_payload):
        valid_payload['authority'] = 'invalid.com'
        pyramid_request.json_body = valid_payload

        with pytest.raises(ValidationError, match="does not match client authority"):
            create(pyramid_request)

    def test_it_proxies_uniqueness_check_to_service(self, valid_payload, pyramid_request, user_unique_svc, CreateUserAPISchema, auth_client):
        pyramid_request.json_body = valid_payload
        CreateUserAPISchema().validate.return_value = valid_payload

        create(pyramid_request)

        user_unique_svc.ensure_unique.assert_called_with(valid_payload, authority=auth_client.authority)

    def test_raises_conflict_error_from_duplicate_user_error(self, valid_payload, pyramid_request, user_unique_svc):
        pyramid_request.json_body = valid_payload
        user_unique_svc.ensure_unique.side_effect = DuplicateUserError('nope')

        with pytest.raises(ConflictError) as exc:
            create(pyramid_request)

        assert 'nope' in str(exc.value)

    def test_raises_for_invalid_json_body(self, pyramid_request, patch):
        type(pyramid_request).json_body = mock.PropertyMock(side_effect=ValueError())

        with pytest.raises(PayloadError):
            create(pyramid_request)

    @pytest.fixture
    def client_authority(self, patch):
        client_authority = patch('h.views.api.users.client_authority')
        client_authority.return_value = 'weylandindustries.com'
        return client_authority

    @pytest.fixture
    def valid_payload(self):
        return {
            'authority': 'weylandindustries.com',
            'email': 'jeremy@weylandtech.com',
            'username': 'jeremy',
            'display_name': 'Jeremy Weyland',
            'identities': [{
                'provider': 'provider_a',
                'provider_unique_id': 'abc123'
            }],
        }


@pytest.mark.usefixtures('auth_client',
                         'user_svc',
                         'user')
class TestUpdate(object):
    def test_it_updates_display_name(self, pyramid_request, valid_payload, user):
        pyramid_request.json_body = valid_payload
        update(user, pyramid_request)

        assert user.display_name == 'Jeremy Weyland'

    def test_it_updates_email(self, pyramid_request, valid_payload, user):
        pyramid_request.json_body = valid_payload
        update(user, pyramid_request)

        assert user.email == 'jeremy@weylandtech.com'

    def test_you_can_update_the_displayname_of_a_user_who_has_no_email(
            self, factories, pyramid_request, user_svc, valid_payload):
        user = factories.User(display_name='old_display_name', email=None)
        user_svc.fetch.return_value = user
        user_svc.fetch.side_effect = None
        del valid_payload['email']
        valid_payload['display_name'] = 'new_display_name'
        pyramid_request.json_body = valid_payload

        update(user, pyramid_request)

        assert user.display_name == 'new_display_name'
        assert user.email is None

    def test_you_can_add_an_email_to_a_user_who_has_no_email(
            self, factories, pyramid_request, user_svc, valid_payload):
        user = factories.User(email=None)
        user_svc.fetch.return_value = user
        user_svc.fetch.side_effect = None
        del valid_payload['display_name']
        valid_payload['email'] = 'new@new.com'
        pyramid_request.json_body = valid_payload

        update(user, pyramid_request)

        assert user.email == 'new@new.com'

    def test_it_presents_user(self, pyramid_request, valid_payload, user, presenter):
        pyramid_request.json_body = valid_payload
        update(user, pyramid_request)

        presenter.assert_called_once_with(user)

    def test_it_returns_presented_user(self, pyramid_request, valid_payload, presenter):
        pyramid_request.json_body = valid_payload
        result = update(user, pyramid_request)

        assert result == presenter.return_value.asdict()

    def test_it_validates_the_input(self, user, pyramid_request, valid_payload, UpdateUserAPISchema):
        update_schema = UpdateUserAPISchema.return_value
        update_schema.validate.return_value = valid_payload
        pyramid_request.json_body = valid_payload

        update(user, pyramid_request)

        update_schema.validate.assert_called_once_with(valid_payload)

    def test_raises_when_schema_validation_fails(self, user, pyramid_request, valid_payload, UpdateUserAPISchema):
        update_schema = UpdateUserAPISchema.return_value
        update_schema.validate.side_effect = ValidationError('validation failed')

        pyramid_request.json_body = valid_payload

        with pytest.raises(ValidationError):
            update(user, pyramid_request)

    def test_raises_for_invalid_json_body(self, user, pyramid_request, patch):
        type(pyramid_request).json_body = mock.PropertyMock(side_effect=ValueError())

        with pytest.raises(PayloadError):
            update(user, pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.matchdict['username'] = user.username
        return pyramid_request

    @pytest.fixture
    def valid_payload(self):
        return {
            'email': 'jeremy@weylandtech.com',
            'display_name': 'Jeremy Weyland',
        }

    @pytest.fixture
    def user_svc(self, pyramid_config, user):
        svc = mock.Mock(spec_set=['fetch'])

        def fake_fetch(username, authority):
            if (username == user.username and
                    authority == user.authority):
                return user
        svc.fetch.side_effect = fake_fetch

        pyramid_config.register_service(svc, name='user')
        return svc


@pytest.fixture
def auth_client(factories):
    return factories.ConfidentialAuthClient(authority='weylandindustries.com',
                                            grant_type=GrantType.client_credentials)


@pytest.fixture
def user_signup_service(db_session, pyramid_config, user):
    service = mock.Mock(spec_set=UserSignupService(default_authority='example.com',
                                              mailer=None,
                                              session=None,
                                              password_service=None,
                                              signup_email=None,
                                              stats=None))
    service.signup.return_value = user
    pyramid_config.register_service(service, name='user_signup')
    return service


@pytest.fixture
def user_unique_svc(pyramid_config):
    svc = mock.create_autospec(UserUniqueService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name='user_unique')
    return svc


@pytest.fixture
def CreateUserAPISchema(patch):
    return patch('h.views.api.users.CreateUserAPISchema')


@pytest.fixture
def UpdateUserAPISchema(patch):
    return patch('h.views.api.users.UpdateUserAPISchema')


@pytest.fixture
def presenter(patch):
    return patch('h.views.api.users.UserJSONPresenter')


@pytest.fixture
def user(factories, auth_client):
    return factories.User(authority=auth_client.authority)
