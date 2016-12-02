# -*- coding: utf-8 -*-

"""Shared components used across multiple pages on the site."""

from __future__ import unicode_literals

from pyramid_layout.panel import panel_config

from h import i18n
from h._compat import urlparse

_ = i18n.TranslationString


def _matches_route(path, request, route_name):
    """
    Return ``True`` if ``path`` matches the URL pattern for a given route.
    """

    introspector = request.registry.introspector

    # `route` is a pyramid.interfaces.IRoute
    route = introspector.get('routes', route_name)['object']
    return route.match(path) is not None


@panel_config(name='group_invite',
              renderer='h:templates/panels/group_invite.html.jinja2')
def group_invite(context, request, group_url):
    return {'group_url': group_url}


@panel_config(name='back_link',
              renderer='h:templates/panels/back_link.html.jinja2')
def back_link(context, request):
    """
    A link which takes the user back to the previous page on the site.
    """

    referrer_path = urlparse.urlparse(request.referrer or '').path
    current_username = request.authenticated_user.username

    if referrer_path == request.route_path('activity.user_search',
                                           username=current_username):
        back_label = _('Back to your profile page')
    elif _matches_route(referrer_path, request, 'group_read'):
        back_label = _('Back to group overview page')
    else:
        back_label = None

    return {
        'back_label': back_label,
        'back_location': request.referrer,
    }


@panel_config(name='navbar', renderer='h:templates/panels/navbar.html.jinja2')
def navbar(context, request, opts={}):
    """
    The navigation bar displayed at the top of the page.
    """

    groups_menu_items = []
    user_activity_url = None
    username = None

    if request.authenticated_user:
        for group in request.authenticated_user.groups:
            groups_menu_items.append({
                'title': group.name,
                'link': request.route_url('group_read', pubid=group.pubid, slug=group.slug)
                })
        user_activity_url = request.route_url('activity.user_search',
            username=request.authenticated_user.username)
        username = request.authenticated_user.username

    if request.matched_route.name in ['group_read', 'activity.user_search']:
        search_url = request.current_route_url()
    else:
        search_url = request.route_url('activity.search')

    return {
        'settings_menu_items': [
            {'title': _('Account details'), 'link': request.route_url('account')},
            {'title': _('Edit profile'), 'link': request.route_url('account_profile')},
            {'title': _('Notifications'), 'link': request.route_url('account_notifications')},
            {'title': _('Developer'), 'link': request.route_url('account_developer')},
        ],
        'signout_item': {'title': _('Sign out'), 'link': request.route_url('logout')},
        'groups_menu_items': groups_menu_items,
        'create_group_item':
            {'title': _('Create new group'), 'link': request.route_url('group_create')},
        'username': username,
        'username_url': user_activity_url,
        'search_url': search_url,
        'q': request.params.get('q', ''),
        'opts': opts,
    }
