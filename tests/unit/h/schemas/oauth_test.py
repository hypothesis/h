import pytest

from h.schemas import ValidationError
from h.schemas.oauth import InvalidOAuth2StateParamError, OAuth2RedirectSchema


class TestOAuth2RedirectSchema:
    @pytest.mark.parametrize(
        "input_data,expected_output_data",
        [
            (
                {"code": "test_code", "state": "test_state"},
                {"code": "test_code", "state": "test_state"},
            ),
            (
                # Additional unknown properties are allowed but filtered out.
                {"code": "test_code", "state": "test_state", "foo": "bar"},
                {"code": "test_code", "state": "test_state"},
            ),
        ],
    )
    def test_validate(self, pyramid_request, schema, input_data, expected_output_data):
        pyramid_request.session[schema.state_session_key] = input_data["state"]

        output_data = schema.validate(input_data)

        assert output_data == expected_output_data

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
            pyramid_request.session[schema.state_session_key] = data["state"]

        with pytest.raises(ValidationError, match=message):
            schema.validate(data)

    def test_with_state_mismatch(self, pyramid_request, schema):
        data = {"code": "test_code", "state": "test_state"}
        pyramid_request.session[schema.state_session_key] = "different_test_state"

        with pytest.raises(InvalidOAuth2StateParamError):
            schema.validate(data)

    def test_with_no_state_in_session(self, schema):
        data = {"code": "test_code", "state": "test_state"}

        with pytest.raises(InvalidOAuth2StateParamError):
            schema.validate(data)

    def test_state_param(self, pyramid_request, schema, secrets):
        result = schema.state_param()

        assert result == secrets.token_hex.return_value
        assert pyramid_request.session[schema.state_session_key] == result

    @pytest.fixture
    def schema(self, pyramid_request):
        return OAuth2RedirectSchema(pyramid_request, "test_session_key")

    @pytest.fixture(autouse=True)
    def secrets(self, patch):
        return patch("h.schemas.oauth.secrets")
