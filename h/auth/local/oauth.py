import os

from oauthlib.oauth2 import ClientCredentialsGrant, InvalidClientError
from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.exceptions import BadCSRFToken
from pyramid.interfaces import ISessionFactory
from pyramid.session import check_csrf_token, SignedCookieSessionFactory

from h.api import get_consumer


class SessionGrant(ClientCredentialsGrant):
    def validate_token_request(self, request):
        # bw compat
        persona = request.params.get('persona')
        if persona is not None:
            if persona not in request.session.get('personas', []):
                raise InvalidClientError(request=request)
        else:
            try:
                check_csrf_token(request, token='assertion')
            except BadCSRFToken:
                raise InvalidClientError(request=request)

        request.client = get_consumer(request)

        if request.client is None:
            raise InvalidClientError(request=request)

        request.client_id = request.client_id or request.client.client_id


def session_from_config(settings, prefix='session.'):
    """Return a session factory from the provided settings."""
    secret_key = '{}secret'.format(prefix)
    if secret_key not in settings:
        # Get 32 bytes (256 bits) from a secure source (urandom) as a secret.
        # Pyramid will add a salt to this. The salt and the secret together
        # will still be less than the, and therefore right zero-padded to,
        # 1024-bit block size of the default hash algorithm, sha512. However,
        # 256 bits of random should be more than enough for session secrets.
        settings[secret_key] = os.urandom(32)

    return SignedCookieSessionFactory(settings[secret_key])


def includeme(config):
    config.include('pyramid_oauthlib')
    config.add_grant_type(SessionGrant)

    # Configure the authentication policy
    authn_debug = config.registry.settings.get('debug_authorization')
    authn_policy = SessionAuthenticationPolicy(prefix='', debug=authn_debug)
    config.set_authentication_policy(authn_policy)

    def register():
        if config.registry.queryUtility(ISessionFactory) is None:
            session_factory = session_from_config(config.registry.settings)
            config.registry.registerUtility(session_factory, ISessionFactory)

    config.action(None, register, order=1)
