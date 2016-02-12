# -*- coding: utf-8 -*-
from pyramid.session import SignedCookieSessionFactory

from h import features
from h import models
from h.security import derive_key


def model(request):
    session = {}
    session['csrf'] = request.session.get_csrf_token()
    session['userid'] = request.authenticated_userid
    session['groups'] = _current_groups(request)
    session['features'] = features.all(request)
    session['preferences'] = {}
    user = request.authenticated_user
    if user and not user.sidebar_tutorial_dismissed:
        session['preferences']['show_sidebar_tutorial'] = True
    return session


def pop_flash(request):
    return {k: request.session.pop_flash(k)
            for k in ['error', 'info', 'warning', 'success']}


def _group_sort_key(group):
    """Sort private groups for the session model list"""

    # groups are sorted first by name but also by ID
    # so that multiple groups with the same name are displayed
    # in a consistent order in clients
    return (group.name.lower(), group.pubid)


def _current_groups(request):
    """Return a list of the groups the current user is a member of.

    This list is meant to be returned to the client in the "session" model.

    """
    groups = [
        {'name': 'Public', 'id': '__world__', 'public': True},
    ]
    userid = request.authenticated_userid
    if userid is None:
        return groups
    user = request.authenticated_user
    if user is None:
        return groups
    for group in sorted(user.groups, key=_group_sort_key):
        groups.append({
            'name': group.name,
            'id': group.pubid,
            'url': request.route_url('group_read',
                                     pubid=group.pubid,
                                     slug=group.slug),
        })
    return groups


def includeme(config):
    registry = config.registry
    settings = registry.settings

    session_secret = derive_key(settings['secret_key'], b'h.session')
    session_factory = SignedCookieSessionFactory(session_secret, httponly=True)

    config.set_session_factory(session_factory)
