# -*- coding: utf-8 -*-
from oauthlib import oauth2
from oauthlib.oauth2.rfc6749 import errors

import logging
log = logging.getLogger(__name__)


class JWTBearerGrant(oauth2.ClientCredentialsGrant):
    uri = 'urn:ietf:params:oauth:grant-type:jwt-bearer'

    def validate_token_request(self, request):
        if not getattr(request, 'grant_type'):
            raise errors.InvalidRequestError('Request is missing grant type.',
                                             request=request)

        if not request.grant_type == self.uri:
            raise errors.UnsupportedGrantTypeError(request=request)

        if not getattr(request, 'assertion'):
            raise errors.InvalidRequestError('Request is missing assertion.',
                                             request=request)

        for param in ('grant_type', 'scope'):
            if param in request.duplicate_params:
                raise errors.InvalidRequestError(
                    'Duplicate %s parameter.' % param,
                    request=request)

        if request.client_id or request.client_assertion:
            log.debug('Authenticating client, %r.', request)
            if not self.request_validator.authenticate_client(request):
                log.debug('Invalid client (%r), denying access.', request)
                raise errors.InvalidClientError(request=request)
            else:
                request.client_id = request.client_id or \
                    request.client.client_id

            # Ensure client is authorized use of this grant type
            self.validate_grant_type(request)
        else:
            request.client = None

        self.validate_scopes(request)

        log.debug('Validating assertion %s for client %r.',
                  request.assertion, request.client)
        if not self.request_validator.validate_bearer_token(
                request.assertion, request.scopes, request):
            log.debug('Invalid assertion, %s, for client %r.',
                      request.assertion, request.client)
            raise errors.InvalidGrantError('Invalid assertion.',
                                           request=request)
