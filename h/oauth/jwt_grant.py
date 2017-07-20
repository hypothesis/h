# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from oauthlib.oauth2.rfc6749 import errors
from oauthlib.oauth2.rfc6749.grant_types.base import GrantTypeBase

from h.oauth.jwt_grant_token import JWTGrantToken


class JWTAuthorizationGrant(GrantTypeBase):
    def __init__(self, request_validator, user_svc, domain):
        self.request_validator = request_validator
        self.user_svc = user_svc
        self.domain = domain

    def create_token_response(self, request, token_handler):
        """
        Validate the authorization code.
        """
        headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache',
        }

        try:
            self.validate_token_request(request)
        except errors.OAuth2Error as e:
            return headers, e.json, e.status_code

        token = token_handler.create_token(request, refresh_token=True, save_token=False)
        self.request_validator.save_token(token, request)
        return headers, json.dumps(token), 200

    def validate_token_request(self, request):
        try:
            assertion = request.assertion
        except AttributeError:
            raise errors.InvalidRequestFatalError('Missing assertion.')

        token = JWTGrantToken(assertion)

        # Update client_id in oauthlib request
        request.client_id = token.issuer

        if not self.request_validator.authenticate_client_id(request.client_id, request):
            raise errors.InvalidClientError(request=request)

        # Ensure client is authorized use of this grant type
        self.validate_grant_type(request)

        verified_token = token.verified(key=request.client.secret, audience=self.domain)

        user = self.user_svc.fetch(verified_token.subject)
        if user is None:
            raise errors.InvalidGrantError('Grant token subject (sub) could not be found.')

        if user.authority != request.client.authority:
            raise errors.InvalidGrantError('Grant token subject (sub) does not match issuer (iss).')

        request.user = user
