# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from oauthlib.oauth2 import InvalidGrantError, InvalidRequestFatalError


class MissingJWTGrantTokenClaimError(InvalidGrantError):
    def __init__(self, claim, claim_description=None):
        if claim_description:
            self.description = "Missing claim '{}' ({}) from grant token.".format(claim, claim_description)
        else:
            self.description = "Missing claim '{}' from grant token.".format(claim)


class InvalidJWTGrantTokenClaimError(InvalidGrantError):
    def __init__(self, claim, claim_description=None):
        if claim_description:
            self.description = "Invalid claim '{}' ({}) in grant token.".format(claim, claim_description)
        else:
            self.description = "Invalid claim '{}' in grant token.".format(claim)


class InvalidRefreshTokenError(InvalidRequestFatalError):
    description = 'Invalid refresh_token.'
