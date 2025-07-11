import datetime
from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

JWK_CLIENT_TIMEOUT = 10


class TokenValidationError(Exception):
    """Decoding or validating a JWT failed."""


class JWTService:
    LEEWAY = datetime.timedelta(seconds=10)

    @classmethod
    def decode_token(
        cls, token: str, key_set_url: str, algorithms: list[str]
    ) -> dict[str, Any]:
        try:
            unverified_header = jwt.get_unverified_header(token)
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
        except PyJWTError as err:
            msg = "Invalid JWT {err}"
            raise TokenValidationError(msg) from err

        if not unverified_header.get("kid"):
            msg = "Missing 'kid' value in JWT header"
            raise TokenValidationError(msg)

        iss, aud = unverified_payload.get("iss"), unverified_payload.get("aud")

        try:
            signing_key = cls._get_jwk_client(key_set_url).get_signing_key_from_jwt(
                token
            )

            return jwt.decode(
                token,
                key=signing_key.key,
                audience=aud,
                algorithms=algorithms,
                leeway=cls.LEEWAY,
            )
        except PyJWTError as err:
            msg = f"Invalid JWT for: {iss}, {aud}. {err}"
            raise TokenValidationError(msg) from err

    @staticmethod
    @lru_cache(maxsize=256)
    def _get_jwk_client(jwk_url: str) -> PyJWKClient:
        """Get a PyJWKClient for the given key set URL.

        PyJWKClient maintains a cache of keys it has seen.
        We want to keep the clients around with `lru_cache` to reuse that internal cache.
        """
        return PyJWKClient(jwk_url, cache_keys=True, timeout=JWK_CLIENT_TIMEOUT)


def factory(context, request):
    del context, request

    return JWTService()
