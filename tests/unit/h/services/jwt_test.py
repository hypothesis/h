from unittest.mock import sentinel

import pytest
from jwt.exceptions import InvalidTokenError

from h.services.jwt import JWK_CLIENT_TIMEOUT, JWTService, TokenValidationError


class TestJWTService:
    def test_decode_token(self, jwt, PyJWKClient):
        jwt.decode.return_value = {"aud": "AUD", "iss": "ISS"}
        jwt.get_unverified_header.return_value = {"kid": "KID"}

        payload = JWTService.decode_token(
            sentinel.token, sentinel.key_set_url, sentinel.algorithms
        )

        jwt.get_unverified_header.assert_called_once_with(sentinel.token)
        PyJWKClient.assert_called_once_with(
            sentinel.key_set_url, cache_keys=True, timeout=JWK_CLIENT_TIMEOUT
        )
        jwt.decode.assert_called_with(
            sentinel.token,
            key=PyJWKClient.return_value.get_signing_key_from_jwt.return_value.key,
            audience="AUD",
            algorithms=sentinel.algorithms,
            leeway=JWTService.LEEWAY,
        )
        assert payload == jwt.decode.return_value

    def test_decode_token_with_no_kid(self, jwt):
        jwt.get_unverified_header.return_value = {}

        with pytest.raises(
            TokenValidationError, match="Missing 'kid' value in JWT header"
        ):
            JWTService.decode_token(
                sentinel.token, sentinel.key_set_url, sentinel.algorithms
            )

    def test_decode_token_with_invalid_jwt_header(self, jwt):
        jwt.get_unverified_header.side_effect = InvalidTokenError()

        with pytest.raises(TokenValidationError, match="Invalid JWT"):
            JWTService.decode_token(
                sentinel.token, sentinel.key_set_url, sentinel.algorithms
            )

    def test_decode_token_with_invalid_jwt(self, jwt):
        jwt.decode.side_effect = [{"aud": "AUD", "iss": "ISS"}, InvalidTokenError()]

        with pytest.raises(TokenValidationError, match="Invalid JWT"):
            JWTService.decode_token(
                sentinel.token, sentinel.key_set_url, sentinel.algorightms
            )

    @pytest.fixture(autouse=True)
    def jwt(self, patch):
        return patch("h.services.jwt.jwt")

    @pytest.fixture(autouse=True)
    def PyJWKClient(self, patch):
        return patch("h.services.jwt.PyJWKClient")

    @pytest.fixture(autouse=True)
    def clear_jwk_cache(self):
        JWTService._get_jwk_client.cache_clear()  # noqa: SLF001
