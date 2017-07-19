# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from oauthlib.oauth2 import (
    AuthorizationCodeGrant,
    AuthorizationEndpoint,
    BearerToken,
    RefreshTokenGrant,
    TokenEndpoint,
)

from h.oauth import InvalidRefreshTokenError, JWTAuthorizationGrant
from h.security import token_urlsafe

TOKEN_TTL = datetime.timedelta(hours=1).total_seconds()


class OAuthProviderService(AuthorizationEndpoint, TokenEndpoint):
    def __init__(self, oauth_validator, user_svc, domain):
        self.oauth_validator = oauth_validator

        auth_code_grant = AuthorizationCodeGrant(oauth_validator)
        jwt_auth_grant = JWTAuthorizationGrant(oauth_validator, user_svc, domain)
        refresh_grant = RefreshTokenGrant(oauth_validator)

        refresh_grant.custom_validators.pre_token.append(self.load_client_id_from_refresh_token)

        bearer = BearerToken(oauth_validator,
                             token_generator=self.generate_access_token,
                             expires_in=TOKEN_TTL,
                             refresh_token_generator=self.generate_refresh_token)

        AuthorizationEndpoint.__init__(self,
                                       default_response_type='code',
                                       response_types={'code': auth_code_grant},
                                       default_token_type=bearer)
        TokenEndpoint.__init__(self, default_grant_type='authorization_code',
                               grant_types={
                                   'authorization_code': auth_code_grant,
                                   'refresh_token': refresh_grant,
                                   'urn:ietf:params:oauth:grant-type:jwt-bearer': jwt_auth_grant,
                               },
                               default_token_type=bearer)

    def load_client_id_from_refresh_token(self, request):
        """
        Custom validator which sets the client_id from a given refresh token

        For the refresh token flow, RFC 6749 states that public clients only need
        to be verified when the `client_id` is provided. oauthlib seems to be
        ignoring this and always expecds the `client_id` parameter.
        We need to work around this problem since this is an issue with our
        third-party accounts integration, where the piece of code that is
        refreshing a token is not the same as the piece of code that is initially
        generating a JWT bearer token.

        This custom validator tries to load the token from the database, based on
        the given refresh token string and sets the `client_id` from the model.
        Thus allowing oauthlib to continue verifying that the client still exists.
        """
        if not request.refresh_token:
            return

        token = self.oauth_validator.find_refresh_token(request.refresh_token)
        if token:
            request.client_id = token.authclient.id
        else:
            raise InvalidRefreshTokenError()

    def generate_access_token(self, oauth_request):
        return '5768-{}'.format(token_urlsafe())

    def generate_refresh_token(self, oauth_request):
        return '4657-{}'.format(token_urlsafe())


def oauth_provider_service_factory(context, request):
    validator_svc = request.find_service(name='oauth_validator')
    user_svc = request.find_service(name='user')
    return OAuthProviderService(validator_svc, user_svc, request.domain)
