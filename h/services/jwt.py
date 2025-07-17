from collections.abc import Iterable
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from functools import lru_cache
from typing import Any, TypeVar

import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWTError

JWK_CLIENT_TIMEOUT = 10


class JWTDecodeError(Exception):
    """Decoding or validating a JWT failed."""


class JWTPayloadError(JWTDecodeError):
    """A JWT decoded successfully but the payload wasn't what we expected."""


class JWTAudiences(StrEnum):
    """Strings for use in the `aud` claim when encoding JWTs.

    Use short, unique, meaningless, but recognisable strings for audiences,
    for example:

    MY_AUDIENCE = "meas-did-bluk"

    This allows the constants to be renamed when refactoring code, without
    desiring to change the actual string values (which would invalidate JWTs in
    the wild). These strings aren't secret so they can just be hardcoded in the
    source code. Anyone inspecting the contents of a JWT for debugging can look
    up the strings in the source code, this inconvenience is judged worth the
    benefit of easier renaming and refactoring (inspecting JWT contents is
    rare).

    """

    OIDC_REDIRECT_ORCID = "knop"


class JWTIssuers(StrEnum):
    """Strings for use in the `iss` claim when encoding JWTs.

    As with audiences (see above) use meaningless strings for issuers.

    """

    OIDC_CONNECT_OR_LOGIN_ORCID = "hak"


class JWTService:
    LEEWAY = timedelta(seconds=10)

    def __init__(self, jwt_signing_key):
        self.jwt_signing_key = jwt_signing_key

    @classmethod
    def decode_oidc_idtoken(
        cls, token: str, key_set_url: str, algorithms: list[str]
    ) -> dict[str, Any]:
        """Decode the given OpenID Connect (OIDC) ID token and return the payload."""
        try:
            unverified_header = jwt.get_unverified_header(token)
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
        except PyJWTError as err:
            msg = "Invalid JWT {err}"
            raise JWTDecodeError(msg) from err

        if not unverified_header.get("kid"):
            msg = "Missing 'kid' value in JWT header"
            raise JWTDecodeError(msg)

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
            raise JWTDecodeError(msg) from err

    def encode_symmetric(
        self,
        payload,
        *,
        expires_in: timedelta,
        issuer: JWTIssuers,
        audience: JWTAudiences,
        # Test seams to allow unittests to create invalid tokens.
        _algorithm: str = "HS256",
        _signing_key: str | None = None,
    ) -> str:
        """Return a signed (not encrypted) JWT with the given `payload` as its payload.

        :return: a JWT that can be decoded with the decode_symmetric() method
            below to recover the originally given `payload` object.

            The returned JWT is signed to prevent tampering but is *not*
            encrypted so shouldn't contain any sensitive data.

            Signing is done with a symmetric key that is managed by JWTService.

        :type payload: an instance of any dataclass

        :arg issuer: a string that identifies the specific subsystem of the app
            (e.g. route, or possibly route+use-case if a single route issues
            more than one JWT) that issued the JWT. This provides debugging
            information (if decoding JWTs and inspecting their contents while
            debugging).

        :arg audience: a string that identifies the specific subsystem of the
            app (e.g. route, or possibly route+use-case if a single route
            consumes more than one JWT) that is intended to decode the JWT and
            make use of its payload. This prevents substitution attacks or
            confusions where a JWT meant for one part of the app is
            unintentionally used in another part of the app, and also provides
            debugging information (if decoding JWTs and inspecting their
            contents while debugging).

            If `audience` is an iterable of strings then the token will decode
            successfully if its `aud` claim matches any one of the given
            strings.

        encode_symmetric() and decode_symmetric() intend to provide a reusable
        method for encoding JWTs that is general enough to be applicable in
        many contexts (whenever it would be appropriate to use a
        symmetrically-signed but not encrypted JWT with an expiration time,
        issuer and audience) and that uses good practices, for example:

        * Requiring the JWT to have an expiration time, issuer and audience and
          always verifying these when decoding.
        * Signing all JWTs using a single key that is managed by JWTService, to
          avoid a proliferation of different JWT signing keys in envvars or
          databases. The convenience of a single key is judged worth the
          potential loss of security.
        * Using dataclasses to define the expected payload formats,
          and handling exceptions when invalid payloads are encountered.
        * Having thorough documentation, type annotations, and unittests.
        * Providing a simple, easy to use, and easy to test interface for any
          code that wants to encode or decode JWTs.

        """
        payload_dict = asdict(payload)

        if _algorithm == "none":
            signing_key = None
        elif _signing_key:
            signing_key = _signing_key
        else:
            signing_key = self.jwt_signing_key

        # This is deliberately not mentioned in the docstring or type
        # annotations above because it's not intended to be part of the public
        # interface:
        # If falsey values (e.g. None) are passed for expires_in, issuer
        # or audience they will be omitted. The resulting JWT will fail to
        # decode with the decode_symmetric() method below.
        # This is to allow unittests to generate invalid JWTs.
        if expires_in:
            payload_dict["exp"] = datetime.now(tz=UTC) + expires_in
        if issuer:
            payload_dict["iss"] = issuer
        if audience:
            payload_dict["aud"] = audience

        return jwt.encode(
            payload_dict,
            key=signing_key,  # type: ignore[arg-type]
                              # PyJWT's type annotation is wrong: it's actually
                              # possible and documented (and sometimes even
                              # required) to pass key=None but the type
                              # annotation doesn't allow it.
            algorithm=_algorithm,
        )  # fmt: skip

    # The type of the payload_class argument below is any dataclass and the
    # return type of the decode_symmetric() function is an instance of whatever
    # dataclass was passed as the payload_class argument.
    # Use a TypeVar in order to correctly annotate these.
    ANY_DATACLASS = TypeVar("ANY_DATACLASS")

    def decode_symmetric(
        self,
        token: str,
        *,
        audience: JWTAudiences | Iterable[JWTAudiences],
        payload_class: type[ANY_DATACLASS],
    ) -> ANY_DATACLASS:
        """Decode the given `token` and return the original payload.

        Decodes tokens from the JWTService.encode_symmetric() method above.

        :raise JWTDecodeError: if decoding the JWT fails for any reason, for
            example: because the JWT is invalid, because the signature is
            invalid or missing or uses the wrong signing algorithm, because the
            timeout, issuer or audience is missing or invalid, or because the
            payload is invalid.
        """
        try:
            payload_dict = jwt.decode(
                token,
                self.jwt_signing_key,
                algorithms=["HS256"],
                options={"require": ["exp", "iss", "aud"]},
                audience=audience,
            )
        except InvalidTokenError as err:
            raise JWTDecodeError from err

        del payload_dict["exp"], payload_dict["iss"], payload_dict["aud"]

        try:
            return payload_class(**payload_dict)
        except TypeError as err:
            raise JWTPayloadError from err

    @staticmethod
    @lru_cache(maxsize=256)
    def _get_jwk_client(jwk_url: str) -> PyJWKClient:
        """Get a PyJWKClient for the given key set URL.

        PyJWKClient maintains a cache of keys it has seen.
        We want to keep the clients around with `lru_cache` to reuse that internal cache.
        """
        return PyJWKClient(jwk_url, cache_keys=True, timeout=JWK_CLIENT_TIMEOUT)


def factory(context, request):
    del context
    settings = request.registry.settings

    return JWTService(jwt_signing_key=settings["jwt_signing_key"])
