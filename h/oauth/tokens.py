# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from oauthlib.oauth2 import BearerToken as OAuthlibBearerToken


class BearerToken(OAuthlibBearerToken):
    def __init__(
        self,
        request_validator=None,
        token_generator=None,
        expires_in=None,
        refresh_token_generator=None,
        refresh_token_expires_in=None,
    ):
        super(BearerToken, self).__init__(
            request_validator=request_validator,
            token_generator=token_generator,
            expires_in=expires_in,
            refresh_token_generator=refresh_token_generator,
        )

        self.refresh_token_expires_in = refresh_token_expires_in

    def create_token(self, request, refresh_token=False, save_token=True):
        if request.extra_credentials is None:
            request.extra_credentials = {}
        request.extra_credentials[
            "refresh_token_expires_in"
        ] = self.refresh_token_expires_in

        return super(BearerToken, self).create_token(
            request, refresh_token=refresh_token, save_token=save_token
        )
