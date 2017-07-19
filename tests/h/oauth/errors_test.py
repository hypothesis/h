# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.oauth.errors import (
    InvalidJWTGrantTokenClaimError,
    MissingJWTGrantTokenClaimError,
)


class TestMissingJWTGrantTokenClaimError(object):
    def test_sets_correct_description_with_claim_description(self):
        exc = MissingJWTGrantTokenClaimError('iss', 'issuer')
        assert exc.description == 'Missing grant token issuer (iss).'

    def test_sets_correct_description_without_claim_description(self):
        exc = MissingJWTGrantTokenClaimError('iss')
        assert exc.description == 'Missing grant token iss.'


class TestInvalidJWTGrantTokenClaimError(object):
    def test_sets_correct_description_with_claim_description(self):
        exc = InvalidJWTGrantTokenClaimError('iss', 'issuer')
        assert exc.description == 'Invalid grant token issuer (iss).'

    def test_sets_correct_description_without_claim_description(self):
        exc = InvalidJWTGrantTokenClaimError('iss')
        assert exc.description == 'Invalid grant token iss.'
