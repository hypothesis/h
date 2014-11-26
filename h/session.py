import os

from pyramid.interfaces import ISessionFactory
from pyramid.session import SignedCookieSessionFactory


def session_from_config(settings, prefix='session.'):
    """Return a session factory from the provided settings."""
    secret_key = '{}secret'.format(prefix)
    secret = settings.get(secret_key)
    if secret is None:
        # Get 32 bytes (256 bits) from a secure source (urandom) as a secret.
        # Pyramid will add a salt to this. The salt and the secret together
        # will still be less than the, and therefore right zero-padded to,
        # 1024-bit block size of the default hash algorithm, sha512. However,
        # 256 bits of random should be more than enough for session secrets.
        secret = os.urandom(32)

    return SignedCookieSessionFactory(secret)


def includeme(config):
    def register():
        if config.registry.queryUtility(ISessionFactory) is None:
            session_factory = session_from_config(config.registry.settings)
            config.registry.registerUtility(session_factory, ISessionFactory)

    config.action(None, register, order=1)
