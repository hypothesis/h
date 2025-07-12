from datetime import UTC, datetime, timedelta
from unittest.mock import sentinel

import jwt
import pytest
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAlgorithmError,
    InvalidSignatureError,
    InvalidTokenError,
    MissingRequiredClaimError,
)

from h.services.jwt import JWK_CLIENT_TIMEOUT, JWTService, TokenValidationError, factory


class TestJWTService:
    def test_decode_token(self, service, jwt, PyJWKClient):
        jwt.decode.return_value = {"aud": "AUD", "iss": "ISS"}
        jwt.get_unverified_header.return_value = {"kid": "KID"}

        payload = service.decode_token(
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
            leeway=service.LEEWAY,
        )
        assert payload == jwt.decode.return_value

    def test_decode_token_with_no_kid(self, service, jwt):
        jwt.get_unverified_header.return_value = {}

        with pytest.raises(
            TokenValidationError, match="Missing 'kid' value in JWT header"
        ):
            service.decode_token(
                sentinel.token, sentinel.key_set_url, sentinel.algorithms
            )

    def test_decode_token_with_invalid_jwt_header(self, service, jwt):
        jwt.get_unverified_header.side_effect = InvalidTokenError()

        with pytest.raises(TokenValidationError, match="Invalid JWT"):
            service.decode_token(
                sentinel.token, sentinel.key_set_url, sentinel.algorithms
            )

    def test_decode_token_with_invalid_jwt(self, service, jwt):
        jwt.decode.side_effect = [{"aud": "AUD", "iss": "ISS"}, InvalidTokenError()]

        with pytest.raises(TokenValidationError, match="Invalid JWT"):
            service.decode_token(
                sentinel.token, sentinel.key_set_url, sentinel.algorightms
            )

    def test_encode_decode_idinfo(self, service):
        info = {"foo": 42}

        token = service.encode_idinfo("orcid", info)
        decoded_info = service.decode_idinfo("orcid", token)

        assert decoded_info == info

    def test_decode_idinfo_with_invalid_key(self, service, pyramid_settings):
        token = service.encode_idinfo("orcid", {"foo": 42})
        pyramid_settings["idinfo_signingkey_orcid"] = "invalid_key"

        with pytest.raises(InvalidSignatureError):
            service.decode_idinfo("orcid", token)

    def test_decode_idinfo_with_expired_token(self, service, frozen_time):
        token = service.encode_idinfo("orcid", {"foo": 42})
        frozen_time.tick(delta=timedelta(hours=1, seconds=1))

        with pytest.raises(ExpiredSignatureError):
            service.decode_idinfo("orcid", token)

    def test_decode_idinfo_with_no_expiry_time(self, service, pyramid_settings):
        token_with_no_expiry_time = jwt.encode(
            {"foo": 42}, pyramid_settings["idinfo_signingkey_orcid"], algorithm="HS256"
        )

        with pytest.raises(MissingRequiredClaimError) as exc_info:
            service.decode_idinfo("orcid", token_with_no_expiry_time)

        assert exc_info.value.claim == "exp"

    def test_decode_idinfo_with_wrong_algorithm(self, service):
        expiry_time = datetime.now(tz=UTC) + timedelta(hours=1)
        token_encoded_with_wrong_algorithm = jwt.encode(
            {"exp": expiry_time, "foo": 42}, key=None, algorithm="none"
        )

        with pytest.raises(InvalidAlgorithmError):
            service.decode_idinfo("orcid", token_encoded_with_wrong_algorithm)

    @pytest.fixture
    def jwt(self, patch):
        return patch("h.services.jwt.jwt")

    @pytest.fixture(autouse=True)
    def PyJWKClient(self, patch):
        return patch("h.services.jwt.PyJWKClient")

    @pytest.fixture(autouse=True)
    def clear_jwk_cache(self, service):
        service._get_jwk_client.cache_clear()  # noqa: SLF001

    @pytest.fixture
    def service(self, pyramid_request):
        pyramid_request.registry.settings["idinfo_signingkey_orcid"] = "test_signingkey"
        return JWTService(pyramid_request.registry.settings)


class TestFactory:
    def test_it(self, JWTService, pyramid_request):
        service = factory(sentinel.context, pyramid_request)

        JWTService.assert_called_once_with(pyramid_request.registry.settings)
        assert service == JWTService.return_value

    @pytest.fixture(autouse=True)
    def JWTService(self, patch):
        return patch("h.services.jwt.JWTService")
