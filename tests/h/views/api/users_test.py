from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPConflict

from h.models.auth_client import GrantType
from h.schemas import ValidationError
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
        pyramid_request.json_body = valid_payload

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
        self, pyramid_request, valid_payload, CreateUserAPISchema
    ):
        create_schema = CreateUserAPISchema.return_value
        create_schema.validate.side_effect = ValidationError("validation failed")

        pyramid_request.json_body = valid_payload

        with pytest.raises(ValidationError):
            create(pyramid_request)

    def test_raises_ValidationError_when_authority_mismatch(
        self, pyramid_request, valid_payload
    ):
        valid_payload["authority"] = "invalid.com"
        pyramid_request.json_body = valid_payload

        with pytest.raises(ValidationError, match="does not match client authority"):
            create(pyramid_request)

    def test_raises_HTTPConflict_from_DuplicateUserError(
        self, valid_payload, pyramid_request, user_unique_service
    ):
        pyramid_request.json_body = valid_payload
        user_unique_service.ensure_unique.side_effect = DuplicateUserError("nope")

        with pytest.raises(HTTPConflict) as exc:
            create(pyramid_request)

        assert "nope" in str(exc.value)

    def test_raises_for_invalid_json_body(self, pyramid_request):
        type(pyramid_request).json_body = mock.PropertyMock(side_effect=ValueError())

        with pytest.raises(PayloadError):
            create(pyramid_request)

    @pytest.fixture
    def valid_payload(self):
        return {
            "authority": "weylandindustries.com",
            "email": "jeremy@weylandtech.com",
            "username": "jeremy",
            "display_name": "Jeremy Weyland",
            "identities": [{"provider": "provider_a", "provider_unique_id": "abc123"}],
        }

    @pytest.fixture
    def CreateUserAPISchema(self, patch):
        return patch("h.views.api.users.CreateUserAPISchema")

    @pytest.fixture(autouse=True)
    def client_authority(self, patch):
        client_authority = patch("h.views.api.users.client_authority")
        client_authority.return_value = "weylandindustries.com"
        return client_authority


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
        pyramid_request.json_body = valid_payload
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
    def pyramid_request(self, pyramid_request, user):
        # Add a nominal json_body so that _json_payload() parsing of
        # it doesn't raise
        pyramid_request.json_body = {}
        pyramid_request.matchdict["username"] = user.username
        return pyramid_request

    @pytest.fixture
    def valid_payload(self):
        return {"email": "jeremy@weylandtech.com", "display_name": "Jeremy Weyland"}

    @pytest.fixture(autouse=True)
    def UpdateUserAPISchema(self, patch):
        return patch("h.views.api.users.UpdateUserAPISchema")


@pytest.fixture
def auth_client(factories):
    return factories.ConfidentialAuthClient(
        authority="weylandindustries.com", grant_type=GrantType.client_credentials
    )


@pytest.fixture(autouse=True)
def TrustedUserJSONPresenter(patch):
    return patch("h.views.api.users.TrustedUserJSONPresenter")


@pytest.fixture
def user(factories, auth_client):
    return factories.User(authority=auth_client.authority)


@pytest.fixture
def context(user):
    return UserContext(user=user)
