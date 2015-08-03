# -*- coding: utf-8 -*-
from pyramid.session import SignedCookieSessionFactory

from h import models
from h.security import derive_key


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
    groups = [
        {'name': 'Public', 'hashid': '__world__', 'public': True},
    ]
    userid = request.authenticated_userid
    if userid is None:
        return groups
    user = models.User.get_by_userid(request.domain, userid)
    if user is None:
        return groups
    for group in user.groups:
        groups.append({
            'name': group.name,
            'hashid': group.hashid,
            'url': request.route_url('group_read',
                                     hashid=group.hashid,
                                     slug=group.slug),
        })
    return groups


def includeme(config):
    registry = config.registry
    settings = registry.settings

    session_secret = derive_key(settings['secret_key'], 'h.session')
    session_factory = SignedCookieSessionFactory(session_secret, httponly=True)

    config.set_session_factory(session_factory)
