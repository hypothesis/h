# -*- coding: utf-8 -*-

"""Views serving the homepage and related endpoints."""

from __future__ import unicode_literals

from pyramid import httpexceptions
from pyramid.view import view_config


@view_config(route_name='via_redirect', request_method='GET')
def via_redirect(context, request):
    url = request.params.get('url')

    if url is None:
        raise httpexceptions.HTTPBadRequest('"url" parameter missing')

    via_link = 'https://via.hypothes.is/{}'.format(url)
    raise httpexceptions.HTTPFound(location=via_link)


@view_config(route_name='index',
             request_method='GET',
             renderer='h:templates/home.html.jinja2')
def index(context, request):
    context = {}

    if request.user:
        username = request.user.username
        context['username'] = username
        context['user_account_link'] = (
            request.route_url('stream.user_query', user=username)
        )

    return context
