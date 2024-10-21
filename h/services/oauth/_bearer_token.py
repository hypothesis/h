from oauthlib.oauth2 import BearerToken as OAuthlibBearerToken


class BearerToken(OAuthlibBearerToken):  # pylint: disable=abstract-method
    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        request_validator=None,
        token_generator=None,
        expires_in=None,
        refresh_token_generator=None,
        refresh_token_expires_in=None,
    ):
        super().__init__(
            request_validator=request_validator,
            token_generator=token_generator,
            expires_in=expires_in,
            refresh_token_generator=refresh_token_generator,
        )

        self.refresh_token_expires_in = refresh_token_expires_in

    def create_token(self, request, refresh_token=False, **kwargs):
        if request.extra_credentials is None:
            request.extra_credentials = {}
        request.extra_credentials["refresh_token_expires_in"] = (
            self.refresh_token_expires_in
        )

        return super().create_token(request, refresh_token=refresh_token)
