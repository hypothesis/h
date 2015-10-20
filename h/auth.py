# -*- coding: utf-8 -*-
"""
OAuth integration.

Supported grant types
---------------------

- A client credentials grant using the session and authenticating the client
  with cross-site request forgery tokens.

- A JSON Web Token Bearer Grant using the JSON Web Token Profile for OAuth 2.0
  Client Authentication and Authorization Grants [jwt-bearer]_.

.. [jwt-bearer] https://tools.ietf.org/html/draft-ietf-oauth-jwt-bearer


Supported token types
---------------------

- JSON Web Tokens [jwt]_ as bearer tokens.

.. [jwt] https://tools.ietf.org/html/draft-ietf-oauth-json-web-token

Limitations
-----------

- No support for 3rd party clients exists yet.
- No support for scopes yet.

"""
import datetime

import jwt
from jwt.compat import constant_time_compare
from oauthlib.common import generate_client_id
from oauthlib.oauth2 import RequestValidator as _RequestValidator
from pyramid.exceptions import BadCSRFToken
from pyramid import security
from pyramid import session

from pyramid.util import action_method

from .interfaces import IClientFactory
from .oauth import JWT_BEARER
from h import accounts
from h import util
from h.accounts import models
from h.api import groups


LEEWAY = 240  # allowance for clock skew in verification


class RequestValidator(_RequestValidator):

    """Validates JSON Web Tokens."""

    def client_authentication_required(self, request):
        if request.grant_type == JWT_BEARER:
            return False

        return True

    def authenticate_client(self, request):
        client = None
        user = None

        if request.client_id is None:
            try:
                session.check_csrf_token(request, token='assertion')
            except BadCSRFToken:
                return False
            client_id = request.registry.settings['h.client_id']
            client = get_client(request, client_id)
            user = request.authenticated_userid
        elif request.client_secret is not None:
            client_id = request.client_id
            client_secret = request.client_secret
            client = get_client(request, client_id, client_secret)

        request.client = client
        request.user = user
        return request.client is not None

    def save_bearer_token(self, token, request):
        # JWT authorization is stateless
        pass

    def validate_bearer_token(self, token, scopes, request):
        if token is None:
            return False

        try:
            payload = jwt.decode(token, verify=False)
        except jwt.InvalidTokenError:
            return False

        aud = request.host_url
        iss = payload['iss']
        sub = payload.get('sub')

        client = get_client(request, iss)
        if client is None:
            return False

        try:
            payload = jwt.decode(token, key=client.client_secret,
                                 audience=aud, leeway=LEEWAY,
                                 algorithms=['HS256'])

        except jwt.InvalidTokenError:
            return False

        request.client = client
        request.user = sub

        return True

    def validate_grant_type(self, client_id, grant_type, client, request):
        return True

    def get_default_scopes(self, client_id, request):
        return None

    def get_original_scopes(self, assertion, request):
        return None

    def validate_scopes(self, client_id, scopes, client, request):
        return scopes is None


def groupfinder(userid, request):
    """
    Return the list of additional groups of which userid is a member.

    Returns a list of group principals of which the passed userid is a member,
    or None if the userid is not known by this application.
    """
    principals = set()

    user = accounts.get_user(userid, request)
    if user is None:
        return

    if user.admin:
        principals.add('group:__admin__')
    if user.staff:
        principals.add('group:__staff__')
    principals.update(groups.group_principals(user))

    return list(principals)


def effective_principals(userid, request, groupfinder=groupfinder):
    """
    Return the list of effective principals for the passed userid.

    Usually, we can leave the computation of the full set of effective
    principals to the pyramid authentication policy. Sometimes, however, it can
    be useful to discover the full set of effective principals for a userid
    other than the current authenticated userid. This function replicates the
    normal behaviour of a pyramid authentication policy and can be used for
    that purpose.
    """
    principals = set([security.Everyone])

    groups = groupfinder(userid, request)
    if groups is not None:
        principals.add(security.Authenticated)
        principals.add(userid)
        principals.update(groups)

    return list(principals)


def generate_signed_token(request):
    """Generate a signed JSON Web Token from OAuth attributes of the request.

    A JSON Web Token [jwt]_ is a token that contains a header, describing the
    algorithm used for signing, a set of claims (the payload), and a trailing
    signature.

    .. [jwt] https://tools.ietf.org/html/draft-ietf-oauth-json-web-token
    """
    now = datetime.datetime.utcnow().replace(microsecond=0)
    ttl = datetime.timedelta(seconds=request.expires_in)

    claims = {
        'iss': request.client.client_id,
        'aud': request.host_url,
        'sub': request.user,
        'exp': now + ttl,
        'iat': now,
    }

    claims.update(request.extra_credentials or {})
    return jwt.encode(claims, request.client.client_secret)


def get_client(request, client_id, client_secret=None):
    """Get a :class:`h.oauth.IClient` instance using the configured
    :term:`client factory` and provided ''client_id''.

    Returns the client object created by the factory. Returns ``None`` if the
    factory returns ``None`` or the provided ``client_secret`` parameter
    does not match the ``client_secret`` attribute of the client.
    """
    registry = request.registry
    factory = registry.queryUtility(IClientFactory)
    client = factory(request, client_id)

    if client is None:
        return None

    # Allow a default client, hard-coded in the settings.
    if 'h.client_id' in request.registry.settings:
        if client_id == request.registry.settings['h.client_id']:
            if client.client_secret is None:
                client_secret = request.registry.settings['h.client_secret']
                client.client_secret = client_secret

    if client_secret is not None:
        if not constant_time_compare(client_secret, client.client_secret):
            return None

    return client


@action_method
def set_client_factory(config, factory):
    """Override the :term:`client factory` in the current configuration. The
    ``factory`` argument must support the :class:`h.oauth.IClientFactory`
    interface or be a dotted Python name that points to a client factory.
    """
    def register():
        impl = config.maybe_dotted(factory)
        config.registry.registerUtility(impl, IClientFactory)

    intr = config.introspectable('client factory', None,
                                 config.object_description(factory),
                                 'client factory')
    intr['factory'] = factory
    config.action(IClientFactory, register, introspectables=(intr,))


validator = RequestValidator()


def includeme(config):
    registry = config.registry
    settings = registry.settings

    config.include('pyramid_oauthlib')
    config.add_oauth_param('assertion')

    # Use session credentials as a client credentials authorization grant
    config.add_grant_type('oauthlib.oauth2.ClientCredentialsGrant',
                          request_validator=validator)

    # Use web tokens as an authorization grant
    config.add_grant_type('h.oauth.JWTBearerGrant', JWT_BEARER,
                          request_validator=validator)

    # Use web tokens for resource authorization
    config.add_token_type('oauthlib.oauth2.BearerToken',
                          request_validator=validator,
                          token_generator=generate_signed_token)

    # Configure a default client factory
    client_class = settings.get('auth.client_factory', 'h.models.Client')
    config.add_directive('set_client_factory', set_client_factory)
    config.set_client_factory(client_class)

    # Set default client credentials
    settings.setdefault('h.client_id', generate_client_id())
    settings.setdefault('h.client_secret', generate_client_id())
