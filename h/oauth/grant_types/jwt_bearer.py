# -*- coding: utf-8 -*-
import json

from oauthlib.oauth2 import RequestValidator
from oauthlib.oauth2.rfc6749 import errors, utils
from oauthlib.oauth2.rfc6749.grant_types.base import GrantTypeBase

import logging
log = logging.getLogger(__name__)

JWT_BEARER = 'urn:ietf:params:oauth:grant-type:jwt-bearer'


class JWTBearerGrant(GrantTypeBase):

    def __init__(self, request_validator=None):
        self.request_validator = request_validator or RequestValidator()

    def create_token_response(self, request, token_handler):
        headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache',
        }
        try:
            log.debug('Validating access token request, %r.', request)
            self.validate_token_request(request)
        except errors.OAuth2Error as e:
            log.debug('Client error in token request. %s.', e)
            return headers, e.json, e.status_code

        token = token_handler.create_token(request, refresh_token=False)
        return headers, json.dumps(token), 200

    def validate_token_request(self, request):
        if request.grant_type != JWT_BEARER:
            raise errors.UnsupportedGrantTypeError(request=request)

        if request.assertion is None:
            raise errors.InvalidRequestError('Missing assertion parameter.',
                                             request=request)

        for param in ('grant_type', 'scope'):
            if param in request.duplicate_params:
                raise errors.InvalidRequestError(
                    'Duplicate %s parameter.' % param,
                    request=request)

        # Since the JSON Web Token is signed by its issuer client
        # authentication is not strictly required when the token is used as
        # an authorization grant. However, if client credentials are provided
        # they should be validated as describe in Section 3.1.
        # https://tools.ietf.org/html/draft-ietf-oauth-jwt-bearer-12#section-3.1
        if self.request_validator.client_authentication_required(request):
            log.debug('Authenticating client, %r.', request)
            if not self.request_validator.authenticate_client(request):
                log.debug('Invalid client (%r), denying access.', request)
                raise errors.InvalidClientError(request=request)

        # REQUIRED. The web token issued by the client.
        log.debug('Validating assertion %s.', request.assertion)
        if not self.request_validator.validate_bearer_token(
                request.assertion, request.scopes, request):
            log.debug('Invalid assertion, %s, for client %r.',
                      request.assertion, request.client)
            raise errors.InvalidGrantError('Invalid assertion.',
                                           request=request)

        original_scopes = utils.scope_to_list(
            self.request_validator.get_original_scopes(
                request.assertion, request))

        if request.scope:
            request.scopes = utils.scope_to_list(request.scope)
            if (not all((s in original_scopes for s in request.scopes)) and
                not self.request_validator.is_within_original_scope(
                    request.scopes, request.refresh_token, request)):
                log.debug('Refresh token %s lack requested scopes, %r.',
                          request.refresh_token, request.scopes)
                raise errors.InvalidScopeError(request=request)
        else:
            request.scopes = original_scopes
