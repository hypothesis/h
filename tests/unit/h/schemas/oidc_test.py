import pytest

from h.schemas import ValidationError
from h.schemas.oidc import OIDCTokenResponseSchema


class TestOIDCTokenResponseSchema:
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
        return OIDCTokenResponseSchema()
