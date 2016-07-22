# -*- coding: utf-8 -*-

"""
Activity pages views.
"""

from __future__ import unicode_literals

from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h.api import search as search_lib
from h.api.search import parser
from h.api.search import query
from h.api import storage


@view_config(route_name='activity.search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2')
def search(request):
    if not request.feature('activity_pages'):
        raise httpexceptions.HTTPNotFound()

    results = []
    total = None
    tags = []
    if 'q' in request.params:
        search_query = parser.parse(request.params['q'])

        search_request = search_lib.Search(request)
        search_request.append_filter(query.TopLevelAnnotationsFilter())
        search_request.append_aggregation(query.TagsAggregation(limit=10))
        result = search_request.run(search_query)
        total = result.total
        tags = result.aggregations['tags']

        anns = storage.fetch_ordered_annotations(request.db, result.annotation_ids)

        for ann in anns:
            group = request.db.query(models.Group).filter(models.Group.pubid == ann.groupid).one_or_none()
            result = {
                'annotation': ann,
                'group': group,
            }
            results.append(result)

    return {
        'q': request.params.get('q', ''),
        'total': total,
        'results': results,
        'tags': tags,
    }


def includeme(config):
    config.scan(__name__)
