# -*- coding: utf-8 -*-

"""
Activity pages views.
"""

from __future__ import unicode_literals

from pyramid import httpexceptions
from pyramid.view import view_config
from sqlalchemy.orm import subqueryload

from h import models
from h import presenters
from h.activity import bucketing
from memex import search as search_lib
from memex.search import parser
from memex.search import query
from memex import storage


@view_config(route_name='activity.search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2')
def search(request):
    if not request.feature('search_page'):
        raise httpexceptions.HTTPNotFound()

    timeframes = []
    total = None
    tags = []
    users = []
    if 'q' in request.params:
        search_query = parser.parse(request.params['q'])

        search_request = search_lib.Search(request)
        search_request.append_filter(query.TopLevelAnnotationsFilter())
        search_request.append_aggregation(query.TagsAggregation(limit=10))
        if len(search_query.getall('group')) == 1:
            search_request.append_aggregation(query.UsersAggregation(limit=10))
        result = search_request.run(search_query)
        total = result.total
        tags = result.aggregations['tags']
        users = result.aggregations.get('users', [])

        def eager_load_documents(query):
            return query.options(
                subqueryload(models.Annotation.document)
                .subqueryload(models.Document.meta_titles))

        anns = storage.fetch_ordered_annotations(
            request.db, result.annotation_ids,
            query_processor=eager_load_documents)

        timeframes = bucketing.bucket(anns)

        for timeframe in timeframes:
            for document, bucket in timeframe.document_buckets.items():
                for index, annotation in enumerate(bucket.annotations):
                    group = request.db.query(models.Group).filter(
                        models.Group.pubid == annotation.groupid).one_or_none()
                    bucket.annotations[index] = {'annotation': presenters.AnnotationHTMLPresenter(annotation), 'group': group}

    return {
        'q': request.params.get('q', ''),
        'total': total,
        'tags': tags,
        'users': users,
        'timeframes': timeframes,
    }


def includeme(config):
    config.scan(__name__)
