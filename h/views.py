# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import pkg_resources

from pyramid import httpexceptions
from pyramid.view import forbidden_view_config, notfound_view_config
from pyramid.view import view_config
from pyramid import i18n
from pyramid import response

from h import session
from h.api.views import json_view
from h.resources import Annotation
from h.resources import Stream
from h.sidebar import app_config


log = logging.getLogger(__name__)

_ = i18n.TranslationStringFactory(__package__)


def _handle_exc(request):
    request.response.status_int = 500
    request.sentry.captureException()
    # In debug mode we should just reraise, so that the exception is caught by
    # the debug toolbar.
    if request.debug:
        raise


@view_config(context=Exception, accept='text/html',
             renderer='h:templates/5xx.html.jinja2')
def error(context, request):
    """Display an error message."""
    _handle_exc(request)
    return {}


@json_view(context=Exception)
def json_error(context, request):
    """"Return a JSON-formatted error message."""
    _handle_exc(request)
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
        'app_config': app_config(request),
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
    return {
        'app_config': app_config(request),
    }


@view_config(route_name='widget', renderer='h:templates/app.html.jinja2')
def widget(context, request):
    return {
        'app_config': app_config(request)
    }


@view_config(renderer='h:templates/help.html.jinja2', route_name='help')
@view_config(renderer='h:templates/help.html.jinja2', route_name='onboarding')
def help_page(context, request):
    current_route = request.matched_route.name
    return {
        'is_help': current_route == 'help',
        'is_onboarding': current_route == 'onboarding',
    }


@view_config(route_name='robots', http_cache=(86400, {'public': True}))
def robots(context, request):
    fp = pkg_resources.resource_stream(__package__, 'static/robots.txt')
    request.response.content_type = b'text/plain'
    request.response.app_iter = response.FileIter(fp)
    return request.response


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
        'app_config': app_config(request),
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

    config.add_route('embed', '/embed.js')
    config.add_route('widget', '/app.html')

    config.add_route('help', '/docs/help')
    config.add_route('onboarding', '/welcome')
    config.add_route('robots', '/robots.txt')

    config.add_route('session', '/app')
    config.add_route('stream', '/stream')

    config.scan(__name__)
