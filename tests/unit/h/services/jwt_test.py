from dataclasses import dataclass
from datetime import timedelta
from unittest.mock import sentinel

import pytest
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidAlgorithmError,
    InvalidAudienceError,
    InvalidSignatureError,
    InvalidTokenError,
    MissingRequiredClaimError,
)

from h.services.jwt import (
    JWK_CLIENT_TIMEOUT,
    JWTDecodeError,
    JWTPayloadError,
    JWTService,
    factory,
)


class TestJWTService:
    def test_decode_oidc_idtoken(self, service, jwt, PyJWKClient):
        jwt.decode.return_value = {"aud": "AUD", "iss": "ISS"}
        jwt.get_unverified_header.return_value = {"kid": "KID"}

        payload = service.decode_oidc_idtoken(sentinel.token, sentinel.keyset_url)

        jwt.get_unverified_header.assert_called_once_with(sentinel.token)
        PyJWKClient.assert_called_once_with(
            sentinel.keyset_url, cache_keys=True, timeout=JWK_CLIENT_TIMEOUT
        )
        jwt.decode.assert_called_with(
            sentinel.token,
            key=PyJWKClient.return_value.get_signing_key_from_jwt.return_value.key,
            audience="AUD",
            algorithms=["RS256"],
            leeway=service.LEEWAY,
        )
        assert payload == jwt.decode.return_value

    def test_decode_oidc_idtoken_with_no_kid(self, service, jwt):
        jwt.get_unverified_header.return_value = {}

        with pytest.raises(JWTDecodeError, match="Missing 'kid' value in JWT header"):
            service.decode_oidc_idtoken(sentinel.token, sentinel.keyset_url)

    def test_decode_oidc_idtoken_with_invalid_jwt_header(self, service, jwt):
        jwt.get_unverified_header.side_effect = InvalidTokenError()

        with pytest.raises(JWTDecodeError, match="Invalid JWT"):
            service.decode_oidc_idtoken(sentinel.token, sentinel.keyset_url)

    def test_decode_oidc_idtoken_with_invalid_jwt(self, service, jwt):
        jwt.decode.side_effect = [{"aud": "AUD", "iss": "ISS"}, InvalidTokenError()]

        with pytest.raises(JWTDecodeError, match="Invalid JWT"):
            service.decode_oidc_idtoken(sentinel.token, sentinel.keyset_url)

    @dataclass
    class JWTPayload:
        foo: str

    def test_encode_decode_symmetric(self, service, payload):
        token = service.encode_symmetric(
            payload,
            expires_in=timedelta(hours=1),
            issuer="test_issuer",
            audience="test_audience",
        )
        decoded_payload = service.decode_symmetric(
            token,
            audience="test_audience",
            payload_class=TestJWTService.JWTPayload,
        )

        assert decoded_payload == payload

    def test_encode_symmetric_required_kwargs(self, service, payload):
        # The expires_in, issuer and audience arguments are required:
        # encode_symmetric() doesn't support encoding JWTs without these
        # security and debugging features, and decode_symmetric() wouldn't
        # decode one.
        with pytest.raises(
            TypeError,
            match=r"^JWTService\.encode_symmetric\(\) missing 3 required keyword-only arguments: 'expires_in', 'issuer', and 'audience'$",
        ):
            service.encode_symmetric(payload)

    def test_encode_symmetric_keyword_only_args(self, service, payload):
        # To prevent any confusion or mixups expires_in, issuer and
        # audience are keyword-only arguments (payload is the only positional
        # argument).
        with pytest.raises(
            TypeError,
            match=r"^JWTService\.encode_symmetric\(\) takes 2 positional arguments but 5 were given$",
        ):
            service.encode_symmetric(
                payload,
                timedelta(hours=1),
                "test_issuer",
                "test_audience",
            )

    def test_decode_symmetric_required_kwargs(self, service):
        # The issuer, audience and payload_class arguments are required:
        # decode_symmetric() doesn't support decoding JWTs without these
        # security, debugging and code design features.
        with pytest.raises(
            TypeError,
            match=r"^JWTService\.decode_symmetric\(\) missing 2 required keyword-only arguments: 'audience' and 'payload_class'$",
        ):
            service.decode_symmetric("token")

    def test_decode_symmetric_keyword_only_args(self, service):
        # To prevent any confusion or mixups issuer, audience and payload_class
        # are keyword-only arguments (token is the only positional argument).
        with pytest.raises(
            TypeError,
            match=r"^JWTService\.decode_symmetric\(\) takes 2 positional arguments but 4 were given$",
        ):
            service.decode_symmetric(
                "token",
                "audience",
                TestJWTService.JWTPayload,
            )

    def test_decode_symmetric_with_invalid_token(self, service):
        with pytest.raises(JWTDecodeError) as exc_info:
            service.decode_symmetric(
                "invalid_jwt",
                audience="test_audience",
                payload_class=TestJWTService.JWTPayload,
            )

        assert isinstance(exc_info.value.__cause__, DecodeError)

    def test_decode_symmetric_with_expired_token(self, service, payload, frozen_time):
        token = service.encode_symmetric(
            payload,
            expires_in=timedelta(hours=1),
            issuer="test_issuer",
            audience="test_audience",
        )
        frozen_time.tick(delta=timedelta(hours=1, seconds=1))

        with pytest.raises(JWTDecodeError) as exc_info:
            service.decode_symmetric(
                token,
                audience="test_audience",
                payload_class=TestJWTService.JWTPayload,
            )

        assert isinstance(exc_info.value.__cause__, ExpiredSignatureError)

    def test_decode_symmetric_with_no_expiry_time(self, service, payload):
        token = service.encode_symmetric(
            payload,
            expires_in=None,
            issuer="test_issuer",
            audience="test_audience",
        )

        with pytest.raises(JWTDecodeError) as exc_info:
            service.decode_symmetric(
                token,
                audience="test_audience",
                payload_class=TestJWTService.JWTPayload,
            )

        assert isinstance(exc_info.value.__cause__, MissingRequiredClaimError)
        assert exc_info.value.__cause__.claim == "exp"

    def test_decode_symmetric_with_wrong_algorithm(self, service, payload):
        token = service.encode_symmetric(
            payload,
            expires_in=timedelta(hours=1),
            issuer="test_issuer",
            audience="test_audience",
            _algorithm="none",
        )

        with pytest.raises(JWTDecodeError) as exc_info:
            service.decode_symmetric(
                token,
                audience="test_audience",
                payload_class=TestJWTService.JWTPayload,
            )

        assert isinstance(exc_info.value.__cause__, InvalidAlgorithmError)

    def test_decode_symmetric_with_invalid_key(self, service, payload):
        token = service.encode_symmetric(
            payload,
            expires_in=timedelta(hours=1),
            issuer="test_issuer",
            audience="test_audience",
            _signing_key="invalid_key",
        )

        with pytest.raises(JWTDecodeError) as exc_info:
            service.decode_symmetric(
                token,
                audience="test_audience",
                payload_class=TestJWTService.JWTPayload,
            )

        assert isinstance(exc_info.value.__cause__, InvalidSignatureError)

    def test_decode_symmetric_with_no_issuer(self, service, payload):
        token = service.encode_symmetric(
            payload,
            expires_in=timedelta(hours=1),
            issuer=None,
            audience="test_audience",
        )

        with pytest.raises(JWTDecodeError) as exc_info:
            service.decode_symmetric(
                token,
                audience="test_audience",
                payload_class=TestJWTService.JWTPayload,
            )

        assert isinstance(exc_info.value.__cause__, MissingRequiredClaimError)
        assert exc_info.value.__cause__.claim == "iss"

    def test_decode_symmetric_with_wrong_audience(self, service, payload):
        token = service.encode_symmetric(
            payload,
            expires_in=timedelta(hours=1),
            issuer="test_issuer",
            audience="wrong",
        )

        with pytest.raises(JWTDecodeError) as exc_info:
            service.decode_symmetric(
                token,
                audience="test_audience",
                payload_class=TestJWTService.JWTPayload,
            )

        assert isinstance(exc_info.value.__cause__, InvalidAudienceError)

    def test_decode_symmetric_with_no_audience(self, service, payload):
        token = service.encode_symmetric(
            payload,
            expires_in=timedelta(hours=1),
            issuer="test_issuer",
            audience=None,
        )

        with pytest.raises(JWTDecodeError) as exc_info:
            service.decode_symmetric(
                token,
                audience="test_audience",
                payload_class=TestJWTService.JWTPayload,
            )

        assert isinstance(exc_info.value.__cause__, MissingRequiredClaimError)
        assert exc_info.value.__cause__.claim == "aud"

    def test_decode_symmetric_with_invalid_payload(self, service):
        @dataclass
        class InvalidPayload:
            bar: str

        token = service.encode_symmetric(
            InvalidPayload("bar"),
            expires_in=timedelta(hours=1),
            issuer="test_issuer",
            audience="test_audience",
        )

        with pytest.raises(JWTPayloadError):
            service.decode_symmetric(
                token,
                audience="test_audience",
                payload_class=TestJWTService.JWTPayload,
            )

    @pytest.fixture
    def payload(self):
        """Return a payload for testing {encode,decode}_symmetric()."""
        return TestJWTService.JWTPayload("test")

    @pytest.fixture(autouse=True)
    def clear_jwk_cache(self, service):
        service._get_jwk_client.cache_clear()  # noqa: SLF001

    @pytest.fixture
    def service(self):
        return JWTService(jwt_signing_key="test_jwt_signing_key")


class TestFactory:
    def test_it(self, JWTService, pyramid_request):
        pyramid_request.registry.settings["jwt_signing_key"] = sentinel.jwt_signing_key

        service = factory(sentinel.context, pyramid_request)

        JWTService.assert_called_once_with(jwt_signing_key=sentinel.jwt_signing_key)
        assert service == JWTService.return_value

    @pytest.fixture(autouse=True)
    def JWTService(self, patch):
        return patch("h.services.jwt.JWTService")


@pytest.fixture
def jwt(patch):
    return patch("h.services.jwt.jwt")


@pytest.fixture(autouse=True)
def PyJWKClient(patch):
    return patch("h.services.jwt.PyJWKClient")
