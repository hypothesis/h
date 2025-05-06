from functools import lru_cache
from typing import Any

import jwt
import requests
from jwt.exceptions import PyJWTError

from h.schemas import ValidationError


class JWTService:
    def decode_id_token(self, id_token: str, key_set_url: str) -> dict[str, Any]:
        if not id_token:
            return {}

        try:
            unverified_header = jwt.get_unverified_header(id_token)
            unverified_payload = jwt.decode(
                id_token, options={"verify_signature": False}
            )
        except PyJWTError as err:
            raise ValidationError(f"Invalid JWT. {err}") from err  # noqa: EM102, TRY003

        if not unverified_header.get("kid"):
            raise ValidationError("Missing 'kid' value in JWT header")  # noqa: EM101, TRY003

        if not unverified_header.get("alg"):
            raise ValidationError("Missing 'alg' value in JWT header")  # noqa: EM101, TRY003
        alg = unverified_header.get("alg")

        iss, aud = unverified_payload.get("iss"), unverified_payload.get("aud")

        try:
            signing_key = self._get_jwk_client(key_set_url).get_signing_key_from_jwt(
                id_token
            )

            return jwt.decode(
                id_token, key=signing_key.key, audience=aud, algorithms=[alg]
            )
        except PyJWTError as err:
            raise ValidationError(f"Invalid JWT for: {iss}, {aud}. {err}") from err  # noqa: EM102, TRY003

    @staticmethod
    @lru_cache(maxsize=256)
    def _get_jwk_client(jwk_url: str):
        """Get a PyJWKClient for the given key set URL.

        PyJWKClient maintains a cache of keys it has seen.
        We want to keep the clients around with `lru_cache` to reuse that internal cache.
        """
        return _RequestsPyJWKClient(jwk_url, cache_keys=True)


class _RequestsPyJWKClient(jwt.PyJWKClient):
    """Version of PyJWKClient which uses requests to gather JWKs.

    Having our own class and using request allows for easier customization.
    """

    def fetch_data(self):
        with requests.get(
            self.uri, headers={"User-Agent": "requests"}, timeout=(10, 10)
        ) as response:
            return response.json()


def factory(_context, _request):
    return JWTService()
