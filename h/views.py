# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from pyramid import httpexceptions
from pyramid.view import forbidden_view_config, notfound_view_config
from pyramid.view import view_config
from pyramid import i18n

from h import session
from h.api.views import json_view
from h.resources import Annotation
from h.resources import Stream


log = logging.getLogger(__name__)

_ = i18n.TranslationStringFactory(__package__)


@view_config(context=Exception, accept='text/html',
             renderer='h:templates/5xx.html.jinja2')
def error(context, request):
    """Display an error message."""
    log.exception('%s: %s', type(context).__name__, str(context))
    request.response.status_int = 500
    return {}


@json_view(context=Exception)
def json_error(context, request):
    """"Return a JSON-formatted error message."""
    log.exception('%s: %s', type(context).__name__, str(context))
    request.response.status_int = 500
    return {"reason": _(
        "Uh-oh, something went wrong! We're very sorry, our "
        "application wasn't able to load this page. The team has been "
        "notified and we'll fix it shortly. If the problem persists or you'd "
        "like more information please email support@hypothes.is with the "
        "subject 'Internal Server Error'.")}


@view_config(
    context=Annotation,
    permission='read',
    renderer='h:templates/app.html.jinja2',
)
def annotation(context, request):
    annotation = context.model

    if 'title' in annotation.get('document', {}):
        title = 'Annotation by {user} on {title}'.format(
            user=annotation['user'].replace('acct:', ''),
            title=annotation['document']['title'])
    else:
        title = 'Annotation by {user}'.format(
            user=annotation['user'].replace('acct:', ''))

    alternate = request.resource_url(request.root, 'api', 'annotations',
                                     annotation['id'])

    return {
        'meta_attrs': (
            {'property': 'og:title', 'content': title},
            {'property': 'og:description', 'content': ''},
            {'property': 'og:image', 'content': '/assets/images/logo.png'},
            {'property': 'og:site_name', 'content': 'Hypothes.is'},
            {'property': 'og:url', 'content': request.url},
        ),
        'link_attrs': (
            {'rel': 'alternate', 'href': alternate,
                'type': 'application/json'},
        ),
    }


@view_config(route_name='embed', renderer='h:templates/embed.js.jinja2')
def embed(context, request):
    request.response.content_type = b'text/javascript'
    return {}


@view_config(route_name='widget', renderer='h:templates/app.html.jinja2')
def widget(context, request):
    return {}


@view_config(renderer='h:templates/help.html.jinja2', route_name='index')
@view_config(renderer='h:templates/help.html.jinja2', route_name='help')
@view_config(renderer='h:templates/help.html.jinja2', route_name='onboarding')
def help_page(context, request):
    current_route = request.matched_route.name
    return {
        'is_index': current_route == 'index',
        'is_help': current_route == 'help',
        'is_onboarding': current_route == 'onboarding',
    }


@json_view(route_name='session', http_cache=0)
def session_view(request):
    flash = session.pop_flash(request)
    model = session.model(request)
    return dict(status='okay', flash=flash, model=model)


@view_config(context=Stream)
def stream_redirect(context, request):
    location = request.route_url('stream', _query=context['query'])
    raise httpexceptions.HTTPFound(location=location)


@view_config(route_name='stream', renderer='h:templates/app.html.jinja2')
def stream(context, request):
    atom = request.route_url('stream_atom')
    rss = request.route_url('stream_rss')
    return {
        'link_tags': [
            {'rel': 'alternate', 'href': atom, 'type': 'application/atom+xml'},
            {'rel': 'alternate', 'href': rss, 'type': 'application/rss+xml'},
        ]
    }


@forbidden_view_config(renderer='h:templates/notfound.html.jinja2')
@notfound_view_config(renderer='h:templates/notfound.html.jinja2')
def notfound(context, request):
    request.response.status_int = 404
    return {}


def includeme(config):
    config.include('h.assets')

    config.add_route('index', '/')

    config.add_route('embed', '/embed.js')
    config.add_route('widget', '/app.html')

    config.add_route('help', '/docs/help')
    config.add_route('onboarding', '/welcome')

    config.add_route('session', '/app')
    config.add_route('stream', '/stream')

    config.scan(__name__)
