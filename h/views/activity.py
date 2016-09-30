# -*- coding: utf-8 -*-

"""
Activity pages views.
"""

from __future__ import unicode_literals

from pyramid import httpexceptions
from pyramid.view import view_config

from h.activity import query
from h.paginator import paginate

PAGE_SIZE = 200


@view_config(route_name='activity.search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2')
@view_config(route_name='activity.group_search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2')
@view_config(route_name='activity.user_search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2')
def search(request):
    if not request.feature('search_page'):
        raise httpexceptions.HTTPNotFound()

    q = query.extract(request)

    # Check whether a redirect is required
    query.check_url(request, q)

    page_size = request.params.get('page_size', PAGE_SIZE)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = PAGE_SIZE

    # Fetch results
    result = query.execute(request, q, page_size=page_size)

    return {
        'total': result.total,
        'aggregations': result.aggregations,
        'timeframes': result.timeframes,
        'page': paginate(request, result.total, page_size=page_size),
    }
