# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import jwt
from oauthlib.oauth2 import (
    InvalidClientError,
    InvalidGrantError,
    InvalidRequestFatalError,
)

from h.oauth import errors


class JWTGrantToken(object):
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
            self._claims = jwt.decode(token, verify=False)
        except jwt.DecodeError:
            raise InvalidRequestFatalError("Invalid JWT grant token format.")

    @property
    def issuer(self):
        iss = self._claims.get("iss", None)
        if not iss:
            raise errors.MissingJWTGrantTokenClaimError("iss", "issuer")
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
        super(VerifiedJWTGrantToken, self).__init__(token)
        self._verify(key, audience)

    def _verify(self, key, audience):
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
        except TypeError:
            raise InvalidClientError("Client is invalid.")
        except jwt.DecodeError:
            raise InvalidGrantError("Invalid grant token signature.")
        except jwt.exceptions.InvalidAlgorithmError:
            raise InvalidGrantError("Invalid grant token signature algorithm.")
        except jwt.MissingRequiredClaimError as exc:
            if exc.claim == "aud":
                raise errors.MissingJWTGrantTokenClaimError("aud", "audience")
            else:
                raise errors.MissingJWTGrantTokenClaimError(exc.claim)
        except jwt.InvalidAudienceError:
            raise errors.InvalidJWTGrantTokenClaimError("aud", "audience")
        except jwt.ImmatureSignatureError:
            raise InvalidGrantError("Grant token is not yet valid.")
        except jwt.ExpiredSignatureError:
            raise InvalidGrantError("Grant token is expired.")
        except jwt.InvalidIssuedAtError:
            raise InvalidGrantError("Grant token issue time (iat) is in the future.")

    @property
    def expiry(self):
        return self._timestamp_claim("exp", "expiry")

    @property
    def not_before(self):
        return self._timestamp_claim("nbf", "start time")

    def _timestamp_claim(self, key, description):
        claim = self._claims.get(key, None)
        if claim is None:
            raise errors.MissingJWTGrantTokenClaimError(key, description)
        try:
            return datetime.datetime.utcfromtimestamp(claim)
        except (TypeError, ValueError):
            raise errors.InvalidJWTGrantTokenClaimError(key, description)

    @property
    def subject(self):
        sub = self._claims.get("sub", None)
        if not sub:
            raise errors.MissingJWTGrantTokenClaimError("sub", "subject")
        return sub
