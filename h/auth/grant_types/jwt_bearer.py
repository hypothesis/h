# -*- coding: utf-8 -*-
import datetime

import jwt
from oauthlib import oauth2
from oauthlib.oauth2.rfc6749 import errors, utils

import logging
log = logging.getLogger(__name__)

EPOCH = datetime.datetime(1970, 1, 1)
JWT_BEARER = 'urn:ietf:params:oauth:grant-type:jwt-bearer'


def posix_seconds(t):
    return int((t - EPOCH).total_seconds())


class JWTBearerGrant(oauth2.ClientCredentialsGrant):
    def validate_token_request(self, request):
        if not getattr(request, 'grant_type'):
            raise errors.InvalidRequestError('Request is missing grant type.',
                                             request=request)

        if not request.grant_type == JWT_BEARER:
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

        assertion = str(request.params['assertion'])
        log.debug('Validating assertion %s.', assertion)
        try:
            payload = jwt.decode(assertion, verify=False)
        except jwt.DecodeError:
            raise errors.InvalidGrantError('Invalid assertion.',
                                           request=request)

        for claim in ('iss', 'sub', 'aud', 'exp'):
            if claim not in payload:
                raise errors.InvalidGrantError(
                    'Assertion must contain the %s claim.' % claim,
                    request=request)

        now = posix_seconds(datetime.datetime.utcnow())

        if payload['exp'] <= posix_seconds(datetime.datetime.utcnow()):
            raise errors.InvalidGrantError('Invalid assertion.',
                                           request=request)

        if 'nbf' in payload and payload['nbf'] > now:
            raise errors.InvalidGrantError('Invalid assertion.',
                                           request=request)

        if not self.request_validator.validate_web_token(
                assertion, payload, request):
            log.debug('Assertion validation failed, %r.', request)
            raise errors.InvalidGrantError('Invalid assertion.',
                                           request=request)

        original_scopes = utils.scope_to_list(
            self.request_validator.get_original_scopes(assertion, request))

        if request.scope:
            request.scopes = utils.scope_to_list(request.scope)
            if (not all((s in original_scopes for s in request.scopes))
                and not self.request_validator.is_within_original_scope(
                    request.scopes, request.refresh_token, request)):
                log.debug('Refresh token %s lack requested scopes, %r.',
                          request.refresh_token, request.scopes)
                raise errors.InvalidScopeError(request=request)
        else:
            request.scopes = original_scopes
