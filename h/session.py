# -*- coding: utf-8 -*-

from pyramid.session import SignedCookieSessionFactory

from h.security import derive_key


def model(request):
    session = {}
    session['csrf'] = request.session.get_csrf_token()
    session['userid'] = request.authenticated_userid
    session['groups'] = _current_groups(request)
    session['features'] = request.feature.all()
    session['preferences'] = _user_preferences(request.authenticated_user)
    return session


def profile(request):
    """
    Return a representation of the current user's information and settings.
    """
    profile = {}
    profile['userid'] = request.authenticated_userid
    profile['groups'] = _current_groups(request)
    profile['features'] = request.feature.all()
    profile['preferences'] = _user_preferences(request.authenticated_user)
    return profile


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


def _user_preferences(user):
    preferences = {}
    if user and not user.sidebar_tutorial_dismissed:
        preferences['show_sidebar_tutorial'] = True
    return preferences


def includeme(config):
    settings = config.registry.settings

    # By default, derive_key generates a 64-byte (512 bit) secret, which is the
    # correct length for SHA512-based HMAC as specified by the `hashalg`.
    factory = SignedCookieSessionFactory(
        secret=derive_key(settings['secret_key'], b'h.session.cookie_secret'),
        hashalg='sha512',
        httponly=True,
        timeout=3600,
    )
    config.set_session_factory(factory)
