"""
Provides an oauthlib compatible JWT Authorization grant type.

This module provides a grant type implementation that can be used
for the oauthlib token endpoint. It needs to provide a
`create_token_response` method.

The implementation is based on `RFC 7523`_.

Example of how to register the ``JWTAuthorizationGrant`` with oauthlib alongside
the authorization code grant, and the refresh token grant:

::

    class OAuthProvider(AuthorizationEndpoint, TokenEndpoint):

        def __init__(self, oauth_validator, user_svc, domain):

            ...
            jwt_auth_grant = JWTAuthorizationGrant(oauth_validator, user_svc, domain)

            TokenEndpoint.__init__(self, default_grant_type='authorization_code',
                                   grant_types={'authorization_code': ...,
                                                'refresh_token': ...,
                                                'urn:ietf:params:oauth:grant-type:jwt-bearer': jwt_auth_grant},
                                   default_token_type=...)
            ...


For more information, see the `oauthlib documentation`_ on grant types.

.. _`RFC 7523`: https://tools.ietf.org/html/rfc7523
.. _`oauthlib documentation`: http://oauthlib.readthedocs.io/en/latest/oauth2/grants/grants.html
"""

import json

from oauthlib.oauth2.rfc6749 import errors
from oauthlib.oauth2.rfc6749.grant_types.base import GrantTypeBase

from h.services.oauth._jwt_grant_token import JWTGrantToken


class JWTAuthorizationGrant(GrantTypeBase):  # pylint: disable=abstract-method
    def __init__(self, request_validator, user_svc, domain):
        super().__init__(request_validator)
        self.user_svc = user_svc
        self.domain = domain

    def create_token_response(self, request, token_handler):
        """
        Create a new token from a JWT authorization grant.

        If valid and authorized, this creates a new access token and returns
        the token. Otherwise it returns an error response.

        :param request: the oauthlib request
        :type request: oauthlib.common.Request

        :param token_handler: Token generator responding to `create_token`.
        :type token_handler: oauthlib.oauth2.rfc6749.tokens.TokenBase

        :returns: HTTP response tuple: headers, body, status
        :rtype: headers (dict), body (unicode), status (int)
        """

        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        }

        try:
            self.validate_token_request(request)
        except errors.OAuth2Error as err:
            return headers, err.json, err.status_code

        token = token_handler.create_token(request, refresh_token=True)
        self.request_validator.save_token(token, request)

        return headers, json.dumps(token), 200

    def validate_token_request(self, request):
        """
        Validate a token request.

        Sets the ``client_id`` property on the passed-in request to the JWT
        issuer, and finds the user based on the JWT subject and sets it as
        the ``user`` property.

        Raises subclasses of ``oauthlib.oauth2.rfc6749.OAuth2Error`` when
        validation fails.

        :param request: the oauthlib request
        :type request: oauthlib.common.Request
        """

        try:
            assertion = request.assertion
        except AttributeError as err:
            raise errors.InvalidRequestFatalError("Missing assertion.") from err

        token = JWTGrantToken(assertion)

        # Update client_id in oauthlib request
        request.client_id = token.issuer

        if not self.request_validator.authenticate_client_id(
            request.client_id, request
        ):
            raise errors.InvalidClientError(request=request)

        # Ensure client is authorized use of this grant type
        self.validate_grant_type(request)

        authclient = request.client.authclient

        verified_token = token.verified(key=authclient.secret, audience=self.domain)

        user = self.user_svc.fetch(verified_token.subject)
        if user is None:
            raise errors.InvalidGrantError(
                "Grant token subject (sub) could not be found."
            )

        if user.authority != authclient.authority:
            raise errors.InvalidGrantError(
                "Grant token subject (sub) does not match issuer (iss)."
            )

        request.user = user
