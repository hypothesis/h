# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from oauthlib.oauth2 import InvalidGrantError, InvalidRequestFatalError


class MissingJWTGrantTokenClaimError(InvalidGrantError):
    def __init__(self, claim, claim_description=None):
        if claim_description:
            description = "Missing claim '{}' ({}) from grant token.".format(
                claim, claim_description
            )
        else:
            description = "Missing claim '{}' from grant token.".format(claim)
        super(MissingJWTGrantTokenClaimError, self).__init__(description=description)


class InvalidJWTGrantTokenClaimError(InvalidGrantError):
    def __init__(self, claim, claim_description=None):
        if claim_description:
            description = "Invalid claim '{}' ({}) in grant token.".format(
                claim, claim_description
            )
        else:
            description = "Invalid claim '{}' in grant token.".format(claim)
        super(InvalidJWTGrantTokenClaimError, self).__init__(description=description)


class InvalidRefreshTokenError(InvalidRequestFatalError):
    description = "Invalid refresh_token."
