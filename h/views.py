# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from pyramid import httpexceptions
from pyramid.events import ContextFound
from pyramid.view import forbidden_view_config, notfound_view_config
from pyramid.view import view_config
from pyramid import response
from pyramid import i18n

from . import session
from .models import Annotation
from .resources import Application, Stream
from . import api_client
from . import atom_feed

log = logging.getLogger(__name__)

_ = i18n.TranslationStringFactory(__package__)


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
        parts = h.util.split_user(stream_key)
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
        context["link_tags"] = [{
            "rel": "alternate", "href": request.route_url("atom_stream"),
            "type": "application/atom+xml"}]
        return context


def _validate_atom_stream_limit(limit):
    """Validate the given limit and return it as an int.

    The limit should be a number >= 1 as an int, float, string or unicode.

    :param limit: the number to validate
    :type limit: int, float, string or unicode

    :returns: the validated number
    :rtype: int

    :raises ValueError: if ``limit`` is an invalid string that can't be
        converted to an int

    :raises ValueError: if ``limit`` is less than 1

    :raises TypeError: if ``limit`` isn't a string or a number

    """
    if limit in (True, False):
        raise TypeError
    limit = int(limit)
    if limit < 1:
        raise ValueError
    return limit


_ATOM_STREAM_LIMIT_SETTINGS_KEY = "h.stream.atom.limit"


def _validate_default_atom_stream_limit(settings):
    """Validate the h.stream.atom.limit setting.

    Will convert the setting from a string or number to an int.

    Will add "h.stream.atom.limit": 10 into the settings if there's no
    "h.stream.atom.limit" in there.

    :raises RuntimeError: if the setting is invalid

    """
    if _ATOM_STREAM_LIMIT_SETTINGS_KEY in settings:
        limit = settings[_ATOM_STREAM_LIMIT_SETTINGS_KEY]
    else:
        limit = 10
    try:
        settings[_ATOM_STREAM_LIMIT_SETTINGS_KEY] = (
            _validate_atom_stream_limit(limit))
    except (ValueError, TypeError):
        raise RuntimeError(
            '{key} setting is invalid: "{limit}"'.format(
                key=_ATOM_STREAM_LIMIT_SETTINGS_KEY, limit=limit))


def _atom_stream_limit(request):
    """Return the Atom stream limit from the request params, or the default.

    Raises ValueError or TypeError if the URL param is invalid.

    """
    return _validate_atom_stream_limit(
        request.params.get(
            "limit", request.registry.settings.get(
                _ATOM_STREAM_LIMIT_SETTINGS_KEY)))


@view_config(layout='app', route_name='atom_stream')
def atom_stream(request):
    try:
        limit = _atom_stream_limit(request)
    except (ValueError, TypeError):
        raise httpexceptions.HTTPBadRequest(_("Invalid limit param"))

    try:
        annotations = request.api_client.get(
            "/search", params={"limit": limit})["rows"]
    except api_client.ConnectionError as err:
        raise httpexceptions.HTTPServiceUnavailable(err)
    except api_client.Timeout as err:
        raise httpexceptions.HTTPGatewayTimeout(err)

    return response.Response(
        atom_feed.render_feed(
            request,
            atom_feed.augment_annotations(request, annotations),
            atom_url=request.route_url("atom_stream"),
            html_url=request.route_url("stream"),
            title=request.registry.settings.get("h.feed.title"),
            subtitle=request.registry.settings.get("h.feed.subtitle")),
        content_type=b"application/atom+xml")


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

    _validate_default_atom_stream_limit(config.registry.settings)

    config.scan(__name__)
