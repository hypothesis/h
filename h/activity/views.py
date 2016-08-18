# -*- coding: utf-8 -*-

"""
Activity pages views.
"""

from __future__ import unicode_literals

from pyramid import httpexceptions
from pyramid.view import view_config

from memex.search import parser

from h.activity import query


@view_config(route_name='activity.search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2')
def search(request):
    if not request.feature('search_page'):
        raise httpexceptions.HTTPNotFound()

    if 'q' not in request.params:
        return {}

    q = parser.parse(request.params['q'])
    result = query.execute(request, q)

    return {
        'q': request.params['q'],
        'total': result.total,
        'aggregations': result.aggregations,
        'timeframes': result.timeframes,
    }


def includeme(config):
    config.scan(__name__)
