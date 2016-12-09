# -*- coding: utf-8 -*-

"""The navigation bar displayed at the top of most pages."""

from __future__ import unicode_literals

from pyramid_layout.panel import panel_config

from h.i18n import TranslationString as _  # noqa


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
