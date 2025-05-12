import pytest

from h.schemas import ValidationError
from h.schemas.oauth import RetrieveOAuthCallbackSchema, RetrieveOpenIDTokenSchema


class TestRetrieveOAuthCallbackSchema:
    def test_validate(self, pyramid_request, schema):
        data = {"code": "test-code", "state": "test-state"}
        pyramid_request.session["oauth2_state"] = data["state"]

        result = schema.validate(data)

        assert result == data

    def test_validate_with_invalid_state(self, pyramid_request, schema):
        data = {"code": "test-code", "state": "test-state"}
        pyramid_request.session["oauth2_state"] = "different-test-state"

        with pytest.raises(ValidationError, match="Invalid oauth state"):
            schema.validate(data)

    def test_validate_with_missing_state(self, schema):
        data = {"state": "test-state"}

        with pytest.raises(ValidationError, match="Invalid oauth state"):
            schema.validate(data)

    def test_state_param_generates_token(self, pyramid_request, schema, secrets):
        state_token = "test-token"  # noqa: S105
        secrets.token_hex.return_value = state_token

        result = schema.state_param()

        assert result == state_token
        assert pyramid_request.session["oauth2_state"] == state_token

    @pytest.fixture
    def schema(self, pyramid_request):
        return RetrieveOAuthCallbackSchema(pyramid_request)

    @pytest.fixture(autouse=True)
    def secrets(self, patch):
        return patch("h.schemas.oauth.secrets")


class TestRetrieveOpenIDTokenSchema:
    def test_validate(self, schema):
        data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "id_token": "test_id_token",
        }

        result = schema.validate(data)

        assert result == data

    @pytest.mark.parametrize(
        "data,expected_error",
        [
            (
                {
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                    "expires_in": 3600,
                },
                "^'id_token' is a required property$",
            ),
        ],
    )
    def test_validate_with_invalid_data(self, data, expected_error, schema):
        with pytest.raises(ValidationError, match=expected_error):
            schema.validate(data)

    @pytest.fixture
    def schema(self):
        return RetrieveOpenIDTokenSchema()
