# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from oauthlib.oauth2 import InvalidGrantError, InvalidRequestFatalError


class MissingJWTGrantTokenClaimError(InvalidGrantError):
    def __init__(self, claim, claim_description=None):
        if claim_description:
            self.description = 'Missing grant token {} ({}).'.format(claim_description, claim)
        else:
            self.description = 'Missing grant token {}.'.format(claim)


class InvalidJWTGrantTokenClaimError(InvalidGrantError):
    def __init__(self, claim, claim_description=None):
        if claim_description:
            self.description = 'Invalid grant token {} ({}).'.format(claim_description, claim)
        else:
            self.description = 'Invalid grant token {}.'.format(claim)


class InvalidRefreshTokenError(InvalidRequestFatalError):
    description = 'Invalid refresh_token.'
