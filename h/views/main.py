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

from h._compat import urlparse
from h.views.client import render_app


@view_config(route_name='annotation', permission='read')
def annotation_page(annotation, request):
    document = annotation.document
    if document and document.title:
        title = 'Annotation by {user} on {title}'.format(
            user=annotation.userid.replace('acct:', ''),
            title=document.title)
    else:
        title = 'Annotation by {user}'.format(
            user=annotation.userid.replace('acct:', ''))

    alternate = request.route_url('api.annotation', id=annotation.id)

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


@view_config(route_name='stream.tag_query')
def stream_tag_redirect(request):
    query = {'q': 'tag:{}'.format(request.matchdict['tag'])}
    location = request.route_url('stream', _query=query)
    raise httpexceptions.HTTPFound(location=location)


@view_config(route_name='stream.user_query')
def stream_user_redirect(request):
    query = {'q': 'user:{}'.format(request.matchdict['user'])}
    location = request.route_url('stream', _query=query)
    raise httpexceptions.HTTPFound(location=location)


def _html_link(request, annotation):
    """Generate a link to an HTML representation of an annotation."""
    return request.route_url('annotation', id=annotation.id)


def _incontext_link(request, annotation):
    """Generate a link to an annotation on the page where it was made."""
    if not request.feature('direct_linking'):
        return
    try:
        return request.route_url('annotation.incontext', id=annotation.id)
    # A KeyError means that the 'annotation.incontext' route does not
    # exist, which in turn means that a bouncer URL has not been set for
    # this application.
    except KeyError:
        pass


def includeme(config):
    config.scan(__name__)

    # Add a static (i.e. external) route for the bouncer service if we have a
    # URL for a bouncer service set.
    bouncer_url = config.registry.settings.get('h.bouncer_url')
    if bouncer_url:
        bouncer_route = urlparse.urljoin(bouncer_url, '{id}')
        config.add_route('annotation.incontext', bouncer_route, static=True)

    # Add an annotation link generator for the `annotation` view -- this adds a
    # named link called "html" to API rendered views of annotations. See
    # :py:mod:`h.api.presenters` for details.
    config.add_annotation_link_generator('html', _html_link)

    # Add an annotation link generator for viewing annotations in context on
    # the page on which they were made.
    config.add_annotation_link_generator('incontext', _incontext_link)
