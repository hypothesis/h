# -*- coding: utf-8 -*-
import os

from pyramid.session import SignedCookieSessionFactory


def model(request):
    session = {k: v for k, v in request.session.items() if k[0] != '_'}
    session['csrf'] = request.session.get_csrf_token()
    return session


def pop_flash(request):
    session = request.session

    queues = {
        name[3:]: [msg for msg in session.pop_flash(name[3:])]
        for name in session.keys()
        if name.startswith('_f_')
    }

    # Deal with bag.web.pyramid.flash_msg style mesages
    for msg in queues.pop('', []):
        q = getattr(msg, 'kind', '')
        msg = getattr(msg, 'plain', msg)
        queues.setdefault(q, []).append(msg)

    return queues


def set_csrf_token(request, response):
    csrft = request.session.get_csrf_token()
    if request.cookies.get('XSRF-TOKEN') != csrft:
        response.set_cookie('XSRF-TOKEN', csrft)


def session_factory_from_settings(settings, prefix='session.'):
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
    registry = config.registry
    settings = registry.settings
    session_factory = session_factory_from_settings(settings)
    config.set_session_factory(session_factory)
