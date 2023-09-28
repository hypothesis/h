import datetime

import jwt
from oauthlib.oauth2 import (
    InvalidClientError,
    InvalidGrantError,
    InvalidRequestFatalError,
)

from h.services.oauth._errors import (
    InvalidJWTGrantTokenClaimError,
    MissingJWTGrantTokenClaimError,
)


class JWTGrantToken:
    """
    Represents a JWT bearer grant token.

    This class is responsible for a couple of things: firstly, verifying that
    the token is a correctly-formatted JSON Web Token, and that it contains all
    the required claims in the right formats. Some of this processing is
    deferred to the `jwt` module, but that doesn't handle all the fields we
    want to validate.

    """

    def __init__(self, token):
        self._token = token

        try:
            self._claims = jwt.decode(
                token,
                options={"verify_signature": False},
            )
        except jwt.DecodeError as err:
            raise InvalidRequestFatalError("Invalid JWT grant token format.") from err

    @property
    def issuer(self):
        iss = self._claims.get("iss", None)
        if not iss:
            raise MissingJWTGrantTokenClaimError("iss", "issuer")
        return iss

    def verified(self, key, audience):
        return VerifiedJWTGrantToken(self._token, key, audience)


class VerifiedJWTGrantToken(JWTGrantToken):
    """
    Represents a JWT bearer grant token verified with a secret key.

    This exposes more claims than the `GrantToken` superclass, so that it's not
    possible to access the subject ID without first verifying the token.

    """

    MAX_LIFETIME = datetime.timedelta(minutes=10)
    LEEWAY = datetime.timedelta(seconds=10)

    def __init__(self, token, key, audience):
        super().__init__(token)
        self._verify(key, audience)

    def _verify(self, key, audience):  # pylint:disable=too-complex
        if self.expiry - self.not_before > self.MAX_LIFETIME:
            raise InvalidGrantError("Grant token lifetime is too long.")
        try:
            jwt.decode(
                self._token,
                algorithms=["HS256"],
                audience=audience,
                key=key,
                leeway=self.LEEWAY,
            )
        except TypeError as err:
            raise InvalidClientError("Client is invalid.") from err
        except jwt.DecodeError as err:
            raise InvalidGrantError("Invalid grant token signature.") from err
        except jwt.exceptions.InvalidAlgorithmError as err:
            raise InvalidGrantError("Invalid grant token signature algorithm.") from err
        except jwt.MissingRequiredClaimError as err:  # pragma: no cover
            if err.claim == "aud":
                raise MissingJWTGrantTokenClaimError("aud", "audience") from err

            raise MissingJWTGrantTokenClaimError(err.claim) from err
        except jwt.InvalidAudienceError as err:
            raise InvalidJWTGrantTokenClaimError("aud", "audience") from err
        except jwt.ImmatureSignatureError as err:
            raise InvalidGrantError("Grant token is not yet valid.") from err
        except jwt.ExpiredSignatureError as err:
            raise InvalidGrantError("Grant token is expired.") from err
        except jwt.InvalidIssuedAtError as err:  # pragma: no cover
            raise InvalidGrantError(
                "Grant token issue time (iat) is in the future."
            ) from err

    @property
    def expiry(self):
        return self._timestamp_claim("exp", "expiry")

    @property
    def not_before(self):
        return self._timestamp_claim("nbf", "start time")

    def _timestamp_claim(self, key, description):
        claim = self._claims.get(key, None)
        if claim is None:
            raise MissingJWTGrantTokenClaimError(key, description)
        try:
            return datetime.datetime.utcfromtimestamp(claim)
        except (TypeError, ValueError) as err:
            raise InvalidJWTGrantTokenClaimError(key, description) from err

    @property
    def subject(self):
        sub = self._claims.get("sub", None)
        if not sub:
            raise MissingJWTGrantTokenClaimError("sub", "subject")
        return sub
