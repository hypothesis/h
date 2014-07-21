# -*- coding: utf-8 -*-
import json
import logging

from pyramid import httpexceptions
from pyramid.view import view_config, view_defaults

from h import interfaces
from h.models import _
from h.streamer import url_values_from_document

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def pop_flash(request):
    session = request.session

    queues = {
        name[3:]: [msg for msg in session.pop_flash(name[3:])]
        for name in session.keys()
        if name.startswith('_f_')
    }

    # Deal with bag.web.pyramid.flash_msg style mesages
    for msg in queues.pop('', []):
        q = getattr(msg, 'kind', '')
        msg = getattr(msg, 'plain', msg)
        queues.setdefault(q, []).append(msg)

    return queues


def model(request):
    session = request.session
    return dict(csrf=session.get_csrf_token(),
                personas=session.get('personas', []))


@view_config(accept='application/json',  name='app', renderer='json')
def app(request):
    return dict(status='okay', flash=pop_flash(request), model=model(request))


@view_config(accept='application/json', renderer='json',
             context='pyramid.exceptions.BadCSRFToken')
def bad_csrf_token(context, request):
    request.response.status_code = 403
    reason = _('Session is invalid. Please try again.')
    return {
        'status': 'failure',
        'reason': reason,
        'model': model(request),
    }


@view_config(name='embed.js', renderer='templates/embed.txt')
@view_config(layout='app', name='app.html', renderer='templates/app.pt')
@view_config(renderer='templates/help.pt', route_name='help')
@view_config(renderer='templates/home.pt', route_name='index')
@view_config(renderer='templates/pattern_library.pt', route_name='pattern_library')
def page(context, request):
    return {}


@view_defaults(context='h.models.Annotation', layout='annotation')
class AnnotationController(object):
    def __init__(self, request):
        self.request = request
        self.Store = request.registry.getUtility(interfaces.IStoreClass)

    @view_config(accept='text/html', renderer='templates/displayer.pt')
    def __html__(self):
        request = self.request
        context = request.context

        d = url_values_from_document(context)
        d['annotation'] = context

        referrers = self.Store(request).search(references=context['id'])
        d['annotation']['referrers'] = referrers

        if context.get('references', []):
            parent = context.__parent__[context['references'][-1]]
            d['quoteSource'] = 'annotation'
            d['quoteUser'] = parent['user']
            d['quote'] = parent['text']
        else:
            d['quoteSource'] = 'document'
            d['quote'] = context.quote
            context['references'] = []

        if 'deleted' not in context:
            context['deleted'] = False

        context['date'] = context['updated']

        return {'annotation': json.dumps(d)}

    @view_config(accept='application/json', renderer='json')
    def __call__(self):
        return self.request.context


@view_config(
    context='h.interfaces.IStreamResource',
    layout='app',
    renderer='templates/app.pt',
)
def stream(context, request):
    stream_type = context.get('stream_type')
    stream_key = context.get('stream_key')
    query = None

    if stream_type == 'user':
        query = {'user': stream_key}
    elif stream_type == 'tag':
        query = {'tags': stream_key}

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
