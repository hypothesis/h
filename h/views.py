# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import re

from pyramid import httpexceptions
from pyramid.events import ContextFound
from pyramid.view import forbidden_view_config, notfound_view_config
from pyramid.view import view_config

from . import session
from .models import Annotation
from .resources import Application, Stream

log = logging.getLogger(__name__)


@view_config(context=Exception, renderer='h:templates/5xx.html')
def error(context, request):
    """Display an error message."""
    log.exception('%s: %s', type(context).__name__, str(context))
    request.response.status_int = 500
    return {}


@view_config(
    layout='app',
    context=Annotation,
    permission='read',
    renderer='h:templates/app.html',
)
def annotation(context, request):
    if 'title' in context.get('document', {}):
        title = 'Annotation by {user} on {title}'.format(
            user=context['user'].replace('acct:', ''),
            title=context['document']['title'])
    else:
        title = 'Annotation by {user}'.format(
            user=context['user'].replace('acct:', ''))

    alternate = request.resource_url(request.root, 'api', 'annotations',
                                     context['id'])

    description = context.get('text')
    if len(description) > 200:
        description = description[:200] + '...'

    return {
        'meta_attrs': (
            {'property': 'og:title', 'content': title},
            {'property': 'og:description', 'content': description},
            {'property': 'og:image', 'content': '/assets/images/logo.png'},
            {'property': 'og:site_name', 'content': 'Hypothes.is'},
            {'property': 'og:url', 'content': request.url},
        ),
        'link_attrs': (
            {'rel': 'alternate', 'href': alternate,
                'type': 'application/json'},
        ),
    }


@view_config(name='embed.js', renderer='h:templates/embed.js')
def js(context, request):
    request.response.content_type = b'text/javascript'
    return {}


@view_config(layout='app', name='app.html', renderer='h:templates/app.html')
@view_config(layout='app', name='viewer', renderer='h:templates/app.html')
@view_config(layout='app', name='editor', renderer='h:templates/app.html')
@view_config(layout='app', name='page_search', renderer='h:templates/app.html')
def page(context, request):
    return {}


@view_config(renderer='h:templates/help.html', route_name='index')
@view_config(renderer='h:templates/help.html', route_name='help')
@view_config(renderer='h:templates/help.html', route_name='onboarding')
def help_page(context, request):
    current_route = request.matched_route.name
    return {
        'is_index': current_route == 'index',
        'is_help': current_route == 'help',
        'is_onboarding': current_route == 'onboarding',
    }


@view_config(accept='application/json', context=Application, renderer='json')
def session_view(request):
    request.add_response_callback(session.set_csrf_token)
    flash = session.pop_flash(request)
    model = session.model(request)
    return dict(status='okay', flash=flash, model=model)


@view_config(layout='app', context=Stream, renderer='h:templates/app.html')
@view_config(layout='app', route_name='stream',
             renderer='h:templates/app.html')
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


@forbidden_view_config(renderer='h:templates/notfound.html')
@notfound_view_config(renderer='h:templates/notfound.html')
def notfound(context, request):
    # Dispatch ContextFound for pyramid_layout subscriber
    event = ContextFound(request)
    request.context = context
    request.registry.notify(event)
    return {}


def includeme(config):
    config.include('h.assets')
    config.include('h.layouts')
    config.include('h.panels')

    config.add_route('index', '/')
    config.add_route('help', '/docs/help')
    config.add_route('onboarding', '/welcome')
    config.add_route('stream', '/stream')

    config.scan(__name__)
