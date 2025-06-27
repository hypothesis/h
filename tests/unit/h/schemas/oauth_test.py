import pytest

from h.schemas import ValidationError
from h.schemas.oauth import RetrieveOAuthCallbackSchema, RetrieveOpenIDTokenSchema


class TestRetrieveOAuthCallbackSchema:
    @pytest.mark.parametrize(
        "data",
        [
            {"code": "test_code", "state": "test_state"},
            # Additional unknown properties are passed though unvalidated.
            {"code": "test_code", "state": "test_state", "foo": "bar"},
        ],
    )
    def test_validate(self, pyramid_request, schema, data):
        pyramid_request.session["oauth2_state"] = data["state"]

        result = schema.validate(data)

        assert result == data

    @pytest.mark.parametrize(
        "data,message",
        [
            ([1, 2, 3], r"\[1, 2, 3\] is not of type 'object'"),
            ({}, "'code' is a required property, 'state' is a required property"),
            ({"code": "test_code"}, "'state' is a required property"),
            ({"state": "test_state"}, "'code' is a required property"),
            ({"code": 42, "state": "test_state"}, "code: 42 is not of type 'string'"),
            ({"code": "test_code", "state": 26}, "state: 26 is not of type 'string'"),
            (
                {"code": 32, "state": 17},
                "code: 32 is not of type 'string', state: 17 is not of type 'string'",
            ),
        ],
    )
    def test_invalid(self, pyramid_request, schema, data, message):
        if "state" in data:
            pyramid_request.session["oauth2_state"] = data["state"]

        with pytest.raises(ValidationError, match=message):
            schema.validate(data)

    def test_with_state_mismatch(self, pyramid_request, schema):
        data = {"code": "test_code", "state": "test_state"}
        pyramid_request.session["oauth2_state"] = "different_test_state"

        with pytest.raises(ValidationError, match="Invalid oauth state"):
            schema.validate(data)

    def test_with_no_state_in_session(self, schema):
        data = {"code": "test_code", "state": "test_state"}

        with pytest.raises(ValidationError, match="Invalid oauth state"):
            schema.validate(data)

    def test_state_param(self, pyramid_request, schema, secrets):
        result = schema.state_param()

        assert result == secrets.token_hex.return_value
        assert pyramid_request.session["oauth2_state"] == result

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
