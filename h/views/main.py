# -*- coding: utf-8 -*-

"""
Core application views.

Important views which don't form part of any other major feature package.
"""

from __future__ import unicode_literals

import pkg_resources

from pyramid import httpexceptions
from pyramid import response
from pyramid.view import view_config

from h.resources import Annotation
from h.resources import Stream
from h.views.client import render_app


@view_config(context=Annotation, permission='read')
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

    return render_app(request, {
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
    })


@view_config(route_name='robots', http_cache=(86400, {'public': True}))
def robots(context, request):
    fp = pkg_resources.resource_stream('h', 'static/robots.txt')
    request.response.content_type = b'text/plain'
    request.response.app_iter = response.FileIter(fp)
    return request.response


@view_config(route_name='stream')
def stream(context, request):
    atom = request.route_url('stream_atom')
    rss = request.route_url('stream_rss')
    return render_app(request, {
        'link_tags': [
            {'rel': 'alternate', 'href': atom, 'type': 'application/atom+xml'},
            {'rel': 'alternate', 'href': rss, 'type': 'application/rss+xml'},
        ]
    })


@view_config(context=Stream)
def stream_redirect(context, request):
    location = request.route_url('stream', _query=context['query'])
    raise httpexceptions.HTTPFound(location=location)


def includeme(config):
    config.scan(__name__)
