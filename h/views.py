# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import json

from pyramid import httpexceptions
from pyramid.events import ContextFound
from pyramid.view import forbidden_view_config, notfound_view_config
from pyramid.view import view_config
from pyramid import i18n

from . import session
from .models import Annotation
from .resources import Application, Stream
from . import api_client
from . import util

log = logging.getLogger(__name__)

_ = i18n.TranslationStringFactory(__package__)


@view_config(context=Exception, accept='text/html',
             renderer='h:templates/5xx.html')
def error(context, request):
    """Display an error message."""
    log.exception('%s: %s', type(context).__name__, str(context))
    request.response.status_int = 500
    return {}


@view_config(context=Exception, accept='application/json', renderer='json')
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


@view_config(name='embed.js', renderer='h:templates/embed.js')
def js(context, request):
    request.response.content_type = b'text/javascript'
    return {
        'blocklist': json.dumps(request.registry.settings['h.blocklist'])
    }


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
        parts = util.split_user(stream_key)
        if parts is not None and parts[1] == request.domain:
            query = {'q': 'user:{}'.format(parts[0])}
        else:
            query = {'q': 'user:{}'.format(stream_key)}
    elif stream_type == 'tag':
        query = {'q': 'tag:{}'.format(stream_key)}

    if query is not None:
        location = request.resource_url(context, 'stream', query=query)
        return httpexceptions.HTTPFound(location=location)
    else:
        context["link_tags"] = [{
            "rel": "alternate", "href": request.route_url("stream_atom"),
            "type": "application/atom+xml"}]
        return context


@view_config(renderer='annotations_atom', route_name='stream_atom')
def stream_atom(request):
    try:
        annotations = request.api_client.get(
            "/search", params={"limit": 1000})["rows"]
    except api_client.ConnectionError as err:
        raise httpexceptions.HTTPServiceUnavailable(err)
    except api_client.Timeout as err:
        raise httpexceptions.HTTPGatewayTimeout(err)
    except api_client.APIError as err:
        raise httpexceptions.HTTPBadGateway(err)

    return dict(
        annotations=annotations,
        atom_url=request.route_url("stream_atom"),
        html_url=request.route_url("stream"),
        title=request.registry.settings.get("h.feed.title"),
        subtitle=request.registry.settings.get("h.feed.subtitle"))


@forbidden_view_config(renderer='h:templates/notfound.html')
@notfound_view_config(renderer='h:templates/notfound.html')
def notfound(context, request):
    # Dispatch ContextFound for pyramid_layout subscriber
    event = ContextFound(request)
    request.context = context
    request.registry.notify(event)
    return {}


def _validate_blocklist(config):
    """Validate the "h.blocklist" config file setting.

    h.blocklist in the config file should be a JSON object as a string, for
    example:

        h.blocklist = {
          "www.quirksmode.org": {},
          "finance.yahoo.com": {}
        }

    This function replaces the string value on registry.settings with a dict.
    It inserts a default value ({}) if there's nothing in the config file.

    :raises RuntimeError: if the value in the config file is invalid

    """
    try:
        config.registry.settings['h.blocklist'] = json.loads(
            config.registry.settings.get('h.blocklist', '{}'))
    except ValueError as err:
        raise ValueError(
            "The h.blocklist setting in the config file is invalid: " +
            str(err))


def includeme(config):
    config.include('h.assets')
    config.include('h.layouts')
    config.include('h.panels')

    config.add_route('index', '/')
    config.add_route('help', '/docs/help')
    config.add_route('onboarding', '/welcome')
    config.add_route('stream', '/stream')
    config.add_route('stream_atom', '/stream.atom')

    _validate_blocklist(config)

    config.scan(__name__)
