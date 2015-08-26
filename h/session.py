# -*- coding: utf-8 -*-
from pyramid.session import SignedCookieSessionFactory

from h import models
from h.security import derive_key
from h import groups


def model(request):
    session = {}
    session['csrf'] = request.session.get_csrf_token()
    session['userid'] = request.authenticated_userid
    session['groups'] = _current_groups(request)
    return session


def pop_flash(request):
    return {k: request.session.pop_flash(k)
            for k in ['error', 'info', 'warning', 'success']}


def _current_groups(request):
    """Return a list of the groups the current user is a member of.

    This list is meant to be returned to the client in the "session" model.

    """
    current_groups = [
        {'name': 'Public', 'id': '__world__'},  # No 'url'.
    ]
    userid = request.authenticated_userid
    if userid is None:
        return current_groups
    user = models.User.get_by_userid(request.domain, userid)
    if user is None:
        return current_groups
    for group in user.groups:
        current_groups.append(groups.as_dict(request, group))
    return current_groups


def includeme(config):
    registry = config.registry
    settings = registry.settings

    session_secret = derive_key(settings['secret_key'], 'h.session')
    session_factory = SignedCookieSessionFactory(session_secret, httponly=True)

    config.set_session_factory(session_factory)
