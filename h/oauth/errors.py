from oauthlib.oauth2 import InvalidGrantError, InvalidRequestFatalError


class MissingJWTGrantTokenClaimError(InvalidGrantError):
    def __init__(self, claim, claim_description=None):
        if claim_description:
            description = (
                f"Missing claim '{claim}' ({claim_description}) from grant token."
            )
        else:
            description = f"Missing claim '{claim}' from grant token."
        super().__init__(description=description)


class InvalidJWTGrantTokenClaimError(InvalidGrantError):
    def __init__(self, claim, claim_description=None):
        if claim_description:
            description = (
                f"Invalid claim '{claim}' ({claim_description}) in grant token."
            )
        else:
            description = f"Invalid claim '{claim}' in grant token."
        super().__init__(description=description)


class InvalidRefreshTokenError(InvalidRequestFatalError):
    description = "Invalid refresh_token."
