from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPConflict

from h.models.auth_client import GrantType
from h.schemas import ValidationError
from h.security import Identity
from h.services.user_unique import DuplicateUserError
from h.traversal import UserContext
from h.views.api.exceptions import PayloadError
from h.views.api.users import create, read, update


class TestRead:
    def test_it(self, pyramid_request, context, TrustedUserJSONPresenter):
        result = read(context, pyramid_request)

        TrustedUserJSONPresenter.assert_called_once_with(context.user)
        assert result == TrustedUserJSONPresenter.return_value.asdict.return_value


@pytest.mark.usefixtures("user_signup_service", "user_unique_service")
class TestCreate:
    def test_it(
        self,
        pyramid_request,
        user_signup_service,
        user_unique_service,
        auth_client,
        valid_payload,
        CreateUserAPISchema,
        TrustedUserJSONPresenter,
    ):
        CreateUserAPISchema.return_value.validate.return_value = valid_payload

        result = create(pyramid_request)

        CreateUserAPISchema.assert_called_with()
        CreateUserAPISchema.return_value.validate.assert_called_once_with(valid_payload)
        user_unique_service.ensure_unique.assert_called_with(
            valid_payload, authority=auth_client.authority
        )
        user_signup_service.signup.assert_called_once_with(
            require_activation=False, **valid_payload
        )
        user = user_signup_service.signup.return_value
        TrustedUserJSONPresenter.assert_called_with(user)
        TrustedUserJSONPresenter.return_value.asdict.assert_called_once_with()
        assert result == TrustedUserJSONPresenter.return_value.asdict.return_value

    def test_raises_when_schema_validation_fails(
        self, pyramid_request, CreateUserAPISchema
    ):
        CreateUserAPISchema.return_value.validate.side_effect = ValidationError(
            "validation failed"
        )

        with pytest.raises(ValidationError):
            create(pyramid_request)

    def test_raises_ValidationError_when_authority_mismatch(self, pyramid_request):
        pyramid_request.json_body["authority"] = "invalid.com"

        with pytest.raises(ValidationError, match="does not match client authority"):
            create(pyramid_request)

    def test_raises_HTTPConflict_from_DuplicateUserError(
        self, pyramid_request, user_unique_service
    ):
        user_unique_service.ensure_unique.side_effect = DuplicateUserError("nope")

        with pytest.raises(HTTPConflict):
            create(pyramid_request)

    def test_raises_for_invalid_json_body(self, pyramid_request):
        type(pyramid_request).json_body = mock.PropertyMock(side_effect=ValueError())

        with pytest.raises(PayloadError):
            create(pyramid_request)

    @pytest.fixture
    def valid_payload(self, auth_client):
        return {
            "authority": auth_client.authority,
            "email": "jeremy@weylandtech.com",
            "username": "jeremy",
            "display_name": "Jeremy Weyland",
            "identities": [{"provider": "provider_a", "provider_unique_id": "abc123"}],
        }

    @pytest.fixture
    def pyramid_request(self, pyramid_request, valid_payload):
        pyramid_request.json_body = valid_payload
        return pyramid_request

    @pytest.fixture
    def CreateUserAPISchema(self, patch):
        return patch("h.views.api.users.CreateUserAPISchema")


@pytest.mark.usefixtures("user_update_service")
class TestUpdate:
    def test_it(
        self,
        context,
        pyramid_request,
        valid_payload,
        UpdateUserAPISchema,
        user_update_service,
        TrustedUserJSONPresenter,
    ):
        UpdateUserAPISchema.return_value.validate.return_value = valid_payload

        result = update(context, pyramid_request)

        UpdateUserAPISchema.assert_called_with()
        UpdateUserAPISchema.return_value.validate.assert_called_once_with(valid_payload)
        user_update_service.update.assert_called_once_with(
            context.user, **valid_payload
        )

        user = user_update_service.update.return_value
        TrustedUserJSONPresenter.assert_called_with(user)
        TrustedUserJSONPresenter.return_value.asdict.assert_called_once_with()
        assert result == TrustedUserJSONPresenter.return_value.asdict.return_value

    def test_raises_when_schema_validation_fails(
        self, context, pyramid_request, UpdateUserAPISchema
    ):
        UpdateUserAPISchema.return_value.validate.side_effect = ValidationError(
            "validation failed"
        )

        with pytest.raises(ValidationError):
            update(context, pyramid_request)

    def test_raises_for_invalid_json_body(self, context, pyramid_request):
        type(pyramid_request).json_body = mock.PropertyMock(side_effect=ValueError())

        with pytest.raises(PayloadError):
            update(context, pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request, valid_payload):
        pyramid_request.json_body = valid_payload
        return pyramid_request

    @pytest.fixture
    def valid_payload(self):
        return {"email": "jeremy@weylandtech.com", "display_name": "Jeremy Weyland"}

    @pytest.fixture(autouse=True)
    def UpdateUserAPISchema(self, patch):
        return patch("h.views.api.users.UpdateUserAPISchema")


@pytest.fixture
def auth_client(factories):
    return factories.ConfidentialAuthClient(grant_type=GrantType.client_credentials)


@pytest.fixture
def context(factories, auth_client):
    return UserContext(user=factories.User(authority=auth_client.authority))


@pytest.fixture(autouse=True)
def with_auth_client(auth_client, pyramid_config):
    pyramid_config.testing_securitypolicy(
        identity=Identity.from_models(auth_client=auth_client)
    )


@pytest.fixture(autouse=True)
def TrustedUserJSONPresenter(patch):
    return patch("h.views.api.users.TrustedUserJSONPresenter")
