from calendar import timegm
from datetime import datetime, timedelta

import jwt
import pytest
from oauthlib.oauth2 import (
    InvalidClientError,
    InvalidGrantError,
    InvalidRequestFatalError,
)

from h.services.oauth._errors import (
    InvalidJWTGrantTokenClaimError,
    MissingJWTGrantTokenClaimError,
)
from h.services.oauth._jwt_grant_token import JWTGrantToken, VerifiedJWTGrantToken


class TestJWTGrantToken:
    def test_init_decodes_token_without_verifying(self, patch):
        jwt_decode = patch("h.services.oauth._jwt_grant_token.jwt.decode")

        JWTGrantToken("abcdef123456")

        jwt_decode.assert_called_once_with(
            "abcdef123456", options={"verify_signature": False}
        )

    def test_init_raises_for_invalid_token(self):
        with pytest.raises(InvalidRequestFatalError) as exc:
            JWTGrantToken("abcdef123456")

        assert exc.value.description == "Invalid JWT grant token format."

    def test_issuer_returns_iss_claim(self):
        jwttok = jwt_token({"iss": "test-issuer", "foo": "bar"})
        grant_token = JWTGrantToken(jwttok)

        assert grant_token.issuer == "test-issuer"

    def test_issuer_raises_for_missing_iss_claim(self):
        jwttok = jwt_token({"foo": "bar"})
        grant_token = JWTGrantToken(jwttok)

        with pytest.raises(MissingJWTGrantTokenClaimError) as exc:
            _ = grant_token.issuer

        assert exc.value.description == "Missing claim 'iss' (issuer) from grant token."

    def test_verified_initializes_verified_token(self, patch):
        verified_token = patch(
            "h.services.oauth._jwt_grant_token.VerifiedJWTGrantToken"
        )

        jwttok = jwt_token({"iss": "test-issuer"})
        grant_token = JWTGrantToken(jwttok)

        grant_token.verified("top-secret", "test-audience")

        verified_token.assert_called_once_with(jwttok, "top-secret", "test-audience")

    def test_verified_returns_verified_token(self, patch):
        verified_token = patch(
            "h.services.oauth._jwt_grant_token.VerifiedJWTGrantToken"
        )

        jwttok = jwt_token({"iss": "test-issuer"})
        grant_token = JWTGrantToken(jwttok)

        actual = grant_token.verified("top-secret", "test-audience")
        assert actual == verified_token.return_value


class TestVerifiedJWTGrantToken:
    def test_init_returns_token_when_valid(self, claims):
        jwttok = jwt_token(claims)

        actual = VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")
        assert isinstance(actual, VerifiedJWTGrantToken)

    def test_init_raises_for_none_key(self, claims):
        jwttok = jwt_token(claims)

        with pytest.raises(InvalidClientError) as exc:
            VerifiedJWTGrantToken(jwttok, None, "test-audience")

        assert exc.value.description == "Client is invalid."

    def test_init_raises_for_empty_key(self, claims):
        pass

    def test_init_raises_for_too_long_token_lifetime(self, claims):
        claims["exp"] = epoch(delta=timedelta(minutes=15))
        jwttok = jwt_token(claims)

        with pytest.raises(InvalidGrantError) as exc:
            VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")

        assert exc.value.description == "Grant token lifetime is too long."

    def test_init_raises_for_invalid_signature(self, claims):
        jwttok = jwt_token(claims)

        with pytest.raises(InvalidGrantError) as exc:
            VerifiedJWTGrantToken(jwttok, "wrong-secret", "test-audience")

        assert exc.value.description == "Invalid grant token signature."

    def test_init_raises_for_invalid_signature_algorithm(self, claims):
        jwttok = jwt_token(claims, alg="HS512")

        with pytest.raises(InvalidGrantError) as exc:
            VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")

        assert exc.value.description == "Invalid grant token signature algorithm."

    @pytest.mark.parametrize(
        "claim,description",
        [["aud", "audience"], ["exp", "expiry"], ["nbf", "start time"]],
    )
    def test_init_raises_for_missing_claims(self, claims, claim, description):
        del claims[claim]
        jwttok = jwt_token(claims)

        with pytest.raises(InvalidGrantError) as exc:
            VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")

        assert (
            exc.value.description
            == f"Missing claim '{claim}' ({description}) from grant token."
        )

    def test_init_raises_for_invalid_aud(self, claims):
        claims["aud"] = "different-audience"
        jwttok = jwt_token(claims)

        with pytest.raises(InvalidJWTGrantTokenClaimError) as exc:
            VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")

        assert exc.value.description == "Invalid claim 'aud' (audience) in grant token."

    @pytest.mark.parametrize(
        "claim,description", [["exp", "expiry"], ["nbf", "start time"]]
    )
    def test_init_raises_for_invalid_timestamp_types(self, claims, claim, description):
        claims[claim] = "wut"
        jwttok = jwt_token(claims)

        with pytest.raises(InvalidJWTGrantTokenClaimError) as exc:
            VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")

        assert (
            exc.value.description
            == f"Invalid claim '{claim}' ({description}) in grant token."
        )

    def test_init_returns_token_when_expired_but_in_leeway(self, claims):
        claims["exp"] = epoch(delta=timedelta(seconds=-8))
        jwttok = jwt_token(claims)

        VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")

    def test_init_raises_when_expired_with_leeway(self, claims):
        claims["exp"] = epoch(delta=timedelta(minutes=-2))
        jwttok = jwt_token(claims)

        with pytest.raises(InvalidGrantError) as exc:
            VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")

        assert exc.value.description == "Grant token is expired."

    def test_init_raises_for_nbf_claim_in_future(self, claims):
        claims["nbf"] = epoch(delta=timedelta(minutes=2))
        jwttok = jwt_token(claims)

        with pytest.raises(InvalidGrantError) as exc:
            VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")

        assert exc.value.description == "Grant token is not yet valid."

    def test_expiry_returns_exp_claim(self, claims):
        now = datetime.utcnow().replace(microsecond=0)
        delta = timedelta(minutes=2)

        claims["exp"] = epoch(timestamp=now, delta=delta)
        jwttok = jwt_token(claims)

        grant_token = VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")

        assert grant_token.expiry == (now + delta)

    def test_not_before_returns_nbf_claim(self, claims):
        now = datetime.utcnow().replace(microsecond=0)
        delta = timedelta(minutes=-2)

        claims["nbf"] = epoch(timestamp=now, delta=delta)
        jwttok = jwt_token(claims)

        grant_token = VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")

        assert grant_token.not_before == (now + delta)

    def test_subject_returns_sub_claim(self, claims):
        jwttok = jwt_token(claims)

        grant_token = VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")

        assert grant_token.subject == "test-subject"

    def test_subject_raises_for_missing_sub_claim(self, claims):
        del claims["sub"]
        jwttok = jwt_token(claims)

        grant_token = VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")
        with pytest.raises(InvalidGrantError) as exc:
            _ = grant_token.subject

        assert (
            exc.value.description == "Missing claim 'sub' (subject) from grant token."
        )

    def test_subject_raises_for_empty_sub_claim(self, claims):
        claims["sub"] = ""
        jwttok = jwt_token(claims)

        grant_token = VerifiedJWTGrantToken(jwttok, "top-secret", "test-audience")
        with pytest.raises(InvalidGrantError) as exc:
            _ = grant_token.subject

        assert (
            exc.value.description == "Missing claim 'sub' (subject) from grant token."
        )

    @pytest.fixture
    def claims(self):
        """Return claims for a valid JWT token."""

        return {
            "aud": "test-audience",
            "exp": epoch(delta=timedelta(minutes=5)),
            "iss": "test-issuer",
            "nbf": epoch(),
            "sub": "test-subject",
        }


def epoch(timestamp=None, delta=None):
    if timestamp is None:
        timestamp = datetime.utcnow()

    if delta is not None:
        timestamp = timestamp + delta

    return timegm(timestamp.utctimetuple())


def jwt_token(claims, alg="HS256"):
    return jwt.encode(claims, "top-secret", algorithm=alg)
