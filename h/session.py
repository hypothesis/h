# -*- coding: utf-8 -*-
from pyramid.session import SignedCookieSessionFactory

from h import hashids
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
    """
    Return a list of the groups the current user is a member of to be returned
    to the client in the "session" model.
    """
    groups = []
    userid = request.authenticated_userid
    if userid is None:
        return groups
    user = models.User.get_by_id(request, userid)
    if user is None:
        return groups
    for g in user.groups:
        hid = hashids.encode(request, 'h.groups', g.id)
        groups.append({
            'name': g.name,
            'url': request.route_url('group_read', hashid=hid, slug=g.slug),
        })
    return groups


def includeme(config):
    registry = config.registry
    settings = registry.settings

    session_secret = derive_key(settings['secret_key'], 'h.session')
    session_factory = SignedCookieSessionFactory(session_secret)

    config.set_session_factory(session_factory)
