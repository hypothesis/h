# -*- coding: utf-8 -*-

"""Help and documentation views."""

from __future__ import unicode_literals

from pyramid.view import view_config


@view_config(renderer='h:templates/help.html.jinja2', route_name='help')
@view_config(renderer='h:templates/help.html.jinja2', route_name='onboarding')
def help_page(context, request):
    current_route = request.matched_route.name
    return {
        'embed_js_url': request.route_path('embed'),
        'is_help': current_route == 'help',
        'is_onboarding': current_route == 'onboarding',
    }


def includeme(config):
    config.scan(__name__)
