# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from json import loads

from h.oauth.errors import (
    InvalidJWTGrantTokenClaimError,
    MissingJWTGrantTokenClaimError,
)


class TestMissingJWTGrantTokenClaimError(object):
    def test_sets_correct_description_with_claim_description(self):
        exc = MissingJWTGrantTokenClaimError("iss", "issuer")
        assert exc.description == "Missing claim 'iss' (issuer) from grant token."

    def test_sets_correct_description_without_claim_description(self):
        exc = MissingJWTGrantTokenClaimError("iss")
        assert exc.description == "Missing claim 'iss' from grant token."

    def test_serializes_to_json(self):
        exc = MissingJWTGrantTokenClaimError("iss")
        assert loads(exc.json) == {
            "error": "invalid_grant",
            "error_description": "Missing claim 'iss' from grant token.",
        }


class TestInvalidJWTGrantTokenClaimError(object):
    def test_sets_correct_description_with_claim_description(self):
        exc = InvalidJWTGrantTokenClaimError("iss", "issuer")
        assert exc.description == "Invalid claim 'iss' (issuer) in grant token."

    def test_sets_correct_description_without_claim_description(self):
        exc = InvalidJWTGrantTokenClaimError("iss")
        assert exc.description == "Invalid claim 'iss' in grant token."

    def test_serializes_to_json(self):
        exc = InvalidJWTGrantTokenClaimError("iss")
        assert loads(exc.json) == {
            "error": "invalid_grant",
            "error_description": "Invalid claim 'iss' in grant token.",
        }
