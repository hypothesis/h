# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import re
import urlparse

import requests

from pyramid import httpexceptions
from pyramid.events import ContextFound
from pyramid.view import forbidden_view_config, notfound_view_config
from pyramid.view import view_config
import pyramid.i18n

from . import session
from .models import Annotation
from .resources import Application, Stream

log = logging.getLogger(__name__)
_ = pyramid.i18n.TranslationStringFactory(__package__)


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

    return {
        'meta_attrs': (
            {'property': 'og:title', 'content': title},
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


@view_config(layout='app', route_name='atom_stream',
             renderer='h:templates/stream.atom')
def atom_stream(context, request):
    api_url = request.registry.settings.get(
        "h.api_url", request.resource_url(request.root, "api"))

    # TODO: Handle requests failures.
    response = requests.get(
        api_url.rstrip("/") + "/search", params={"limit": 10})

    annotations = response.json()["rows"]

    entries = []
    for annotation in annotations:
        entry = {}
        entry["id"] = request.resource_url(request.root, "a", annotation["id"])
        entry["document_title"] = annotation["document"]["title"]
        entry["updated"] = annotation["updated"]
        entry["created"] = annotation["created"]
        entry["text"] = annotation["text"]

        match = re.match(r'^acct:([^@]+)@(.*)$', annotation["user"])
        username, domain = match.groups()
        entry["username"] = username

        entry["domain"] = urlparse.urlparse(annotation["uri"]).netloc

        def get_selection(annotation):
            for target in annotation["target"]:
                for selector in target["selector"]:
                    if "exact" in selector:
                        return selector["exact"]

        entry["selection"] = get_selection(annotation)

        entry["links"] = [
            {"rel": "alternate", "type": "text/html", "href": entry["id"]},
            {"rel": "alternate", "type": "application/json",
             "href": request.resource_url(
                 request.root, "api", "annotation", annotation["id"])},
        ]

        entries.append(entry)

    return {
        "feed": {
            "id": request.route_url("stream"),
            "title": request.registry.settings.get(
                "h.feed.title", _("Hypothes.is Stream")),
            "subtitle": request.registry.settings.get(
                "h.feed.subtitle", _("The Web. Annotated")),
            "links": [
                {"rel": "self", "type": "application/atom",
                 "href": request.route_url("atom_stream")},
                {"rel": "alternate", "type": "text/html",
                 "href": request.route_url("stream")},
            ],
            "entries": entries,
        },
    }


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
    config.add_route('atom_stream', '/stream.atom')

    config.scan(__name__)
