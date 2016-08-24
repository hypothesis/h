# -*- coding: utf-8 -*-

"""
Core application views.

Important views which don't form part of any other major feature package.
"""

from __future__ import unicode_literals

import logging
import random

from pyramid import httpexceptions
from pyramid import response
from pyramid.view import view_config

from h.models import DebugCounter
from h.views.client import render_app

log = logging.getLogger(__name__)


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
    return response.FileResponse('h/static/robots.txt',
                                 request=request,
                                 content_type=b'text/plain')


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


# FIXME: Remove this. Temporary view for debugging.
@view_config(route_name='debug.counter', renderer='string')
def debug_counter(request):
    setattr(request, '_debug_tm', True)

    _configure_noisy_session_logging(request)

    cnt = request.db.query(DebugCounter).one_or_none()

    if cnt is None:
        cnt = DebugCounter(val=0)
        request.db.add(cnt)
    elif 'reset' in request.params:
        cnt.val = 0

    cnt.val += 1

    return 'count={}'.format(cnt.val)


def _configure_noisy_session_logging(request):
    from sqlalchemy import event

    @event.listens_for(request.db, 'after_attach')
    def after_attach(sess, instance):
        log.info('after_attach sess=%r instance=%r', sess, instance)

    @event.listens_for(request.db, 'after_flush')
    def after_flush(sess, flush_context):
        log.info('after_attach sess=%r flush_context=%r', sess, flush_context)

    @event.listens_for(request.db, 'before_commit')
    def before_commit(sess):
        log.info('before_commit sess=%r', sess)

    @event.listens_for(request.db, 'after_rollback')
    def after_rollback(sess):
        log.info('after_rollback sess=%r', sess)


def includeme(config):
    config.scan(__name__)
