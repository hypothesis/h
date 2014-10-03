# -*- coding: utf-8 -*-
import logging
import re

from pyramid import httpexceptions
from pyramid.view import view_config


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@view_config(
    layout='app',
    context='h.models.Annotation',
    renderer='h:templates/app.pt',
)
def annotation(context, request):
    return {}


@view_config(name='embed.js', renderer='h:templates/embed.txt')
def js(context, request):
    request.response.content_type = 'text/javascript'
    return {}


@view_config(layout='app', name='app.html', renderer='h:templates/app.pt')
@view_config(layout='app', name='viewer', renderer='h:templates/app.pt')
@view_config(layout='app', name='editor', renderer='h:templates/app.pt')
@view_config(layout='app', name='page_search', renderer='h:templates/app.pt')
@view_config(renderer='h:templates/help.pt', route_name='help')
@view_config(renderer='h:templates/home.pt', route_name='index')
def page(context, request):
    return {}


@view_config(
    layout='app',
    context='h.interfaces.IStreamResource',
    renderer='h:templates/app.pt',
)
def stream(context, request):
    stream_type = context.get('stream_type')
    stream_key = context.get('stream_key')
    query = None

    if stream_type == 'user':
        parts = re.match(r'^acct:([^@]+)@(.*)$', stream_key)
        if parts is not None and parts.groups()[1] == request.domain:
            query = {'q': 'user:{}'.format(parts.groups()[0])}
        else:
            query = {'q': 'user:{}'.format(stream_key)}
    elif stream_type == 'tag':
        query = {'q': 'tag:{}'.format(stream_key)}

    if query is not None:
        location = request.resource_url(context, 'stream', query=query)
        return httpexceptions.HTTPFound(location=location)
    else:
        return context


def includeme(config):
    config.include('pyramid_chameleon')

    config.include('h.assets')
    config.include('h.layouts')
    config.include('h.panels')

    config.add_route('index', '/')
    config.add_route('help', '/docs/help')

    config.scan(__name__)
