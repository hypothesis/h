import pytest

from h.schemas import ValidationError
from h.schemas.oauth import InvalidOAuth2StateParamError, OAuth2RedirectSchema


class TestOAuth2RedirectSchema:
    @pytest.mark.parametrize(
        "input_data,expected_state,expected_output_data",
        [
            (
                {"code": "test_code", "state": "test_state"},
                "test_state",
                {"code": "test_code", "state": "test_state"},
            ),
            (
                # Additional unknown properties are allowed but filtered out.
                {"code": "test_code", "state": "test_state", "foo": "bar"},
                "test_state",
                {"code": "test_code", "state": "test_state"},
            ),
        ],
    )
    def test_validate(self, input_data, expected_state, expected_output_data):
        output_data = OAuth2RedirectSchema.validate(input_data, expected_state)

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
    def test_invalid(self, data, message):
        with pytest.raises(ValidationError, match=message):
            OAuth2RedirectSchema.validate(data, "test_state")

    def test_with_state_mismatch(self):
        data = {"code": "test_code", "state": "test_state"}

        with pytest.raises(InvalidOAuth2StateParamError):
            OAuth2RedirectSchema.validate(data, expected_state="different")
