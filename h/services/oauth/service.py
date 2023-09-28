import datetime

from oauthlib.oauth2 import (
    AuthorizationCodeGrant,
    AuthorizationEndpoint,
    RefreshTokenGrant,
    RevocationEndpoint,
    TokenEndpoint,
)

from h.security import token_urlsafe
from h.services.oauth import ACCESS_TOKEN_PREFIX, REFRESH_TOKEN_PREFIX
from h.services.oauth._bearer_token import BearerToken
from h.services.oauth._errors import InvalidRefreshTokenError
from h.services.oauth._jwt_grant import JWTAuthorizationGrant
from h.services.oauth._validator import OAuthValidator

ACCESS_TOKEN_TTL = datetime.timedelta(hours=1).total_seconds()
REFRESH_TOKEN_TTL = datetime.timedelta(days=7).total_seconds()


class OAuthProviderService(AuthorizationEndpoint, RevocationEndpoint, TokenEndpoint):
    """
    The OAuth 2 provider service.

    This service subclasses both the oauthlib `authorization endpoint`_
    and the `token endpoint`_. Its goal is to provide a complete
    configuration on how to provide the necessary functionality of
    an OAuth authorization server.

    .. _`authorization endpoint`: https://oauthlib.readthedocs.io/en/latest/oauth2/endpoints/authorization.html
    .. _`token endpoint`: https://oauthlib.readthedocs.io/en/latest/oauth2/endpoints/token.html
    """

    def __init__(self, oauth_validator, user_svc, domain):
        self.oauth_validator = oauth_validator

        auth_code_grant = AuthorizationCodeGrant(oauth_validator)
        jwt_auth_grant = JWTAuthorizationGrant(oauth_validator, user_svc, domain)

        refresh_grant = RefreshTokenGrant(oauth_validator)
        refresh_grant.custom_validators.pre_token.append(
            self._load_client_id_from_refresh_token
        )

        bearer = BearerToken(
            oauth_validator,
            token_generator=self._generate_access_token,
            expires_in=ACCESS_TOKEN_TTL,
            refresh_token_generator=self._generate_refresh_token,
            refresh_token_expires_in=REFRESH_TOKEN_TTL,
        )

        AuthorizationEndpoint.__init__(
            self,
            default_response_type="code",
            response_types={"code": auth_code_grant},
            default_token_type=bearer,
        )

        TokenEndpoint.__init__(
            self,
            default_grant_type="authorization_code",
            grant_types={
                "authorization_code": auth_code_grant,
                "refresh_token": refresh_grant,
                "urn:ietf:params:oauth:grant-type:jwt-bearer": jwt_auth_grant,
            },
            default_token_type=bearer,
        )

        RevocationEndpoint.__init__(self, oauth_validator)

    def validate_revocation_request(self, request):
        # WARNING! - Don't think because this is here it should be. This is
        # almost certainly a hack on a hack here to prevent the overloaded
        # method from throwing a fit. If you can get rid of this you should.
        """
        Ensure the request is valid.

        We are overriding the base class here to ensure that client_id is in
        place to allow 'unauthenticated' access to the revocation end-point.
        This is because it doesn't really add any security.

        The user can attempt to revoke two types of token: access and refresh

         * If the user has the access token they can obviously pass it as
           the bearer token, so this provides no extra protection
         * If the user has the refresh token, they can use it to get an access
           token, putting us in the previous situation.
        """

        # Read our token and use it to add the client_id to the request to
        # allow authenticate_client_id(request.client_id) to pass in the parent
        if request.token:
            token = self.oauth_validator.find_token(request.token)

            if token:  # pragma: no cover
                request.client_id = token.authclient.id

        # Mark this request as a revocation request so we can know _not_
        # to trigger full client validation later on in
        # OAuthValidatorService.client_authentication_required()
        request.h_revoke_request = True

        return super().validate_revocation_request(request)

    def _load_client_id_from_refresh_token(self, request):
        """
        Add a custom validator which sets the client_id from a given refresh token.

        For the refresh token flow, RFC 6749 states that public clients only need
        to be verified when the `client_id` is provided. oauthlib seems to be
        ignoring this and always expects the `client_id` parameter.
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

    @staticmethod
    def _generate_access_token(oauth_request):  # pylint: disable=unused-argument
        return ACCESS_TOKEN_PREFIX + token_urlsafe()

    @staticmethod
    def _generate_refresh_token(_oauth_request):
        return REFRESH_TOKEN_PREFIX + token_urlsafe()


def factory(_context, request):
    user_svc = request.find_service(name="user")

    return OAuthProviderService(
        oauth_validator=OAuthValidator(session=request.db, user_svc=user_svc),
        user_svc=user_svc,
        domain=request.domain,
    )
