# -*- coding: utf-8 -*-
from pyramid.session import SignedCookieSessionFactory

from .security import derive_key

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


def includeme(config):
    registry = config.registry
    settings = registry.settings

    session_secret = derive_key(settings['secret_key'], 'h.session')
    session_factory = SignedCookieSessionFactory(session_secret)

    config.set_session_factory(session_factory)
