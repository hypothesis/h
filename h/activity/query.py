# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import namedtuple

from memex.search import Search
from memex.search.query import (
    TagsAggregation,
    TopLevelAnnotationsFilter,
    UsersAggregation,
)
from sqlalchemy.orm import subqueryload

from h import presenters
from h.activity import bucketing
from h.models import Annotation, Document, Group


class ActivityResults(namedtuple('ActivityResults', [
    'total',
    'aggregations',
    'timeframes',
])):
    pass


def execute(request, query):
    search = Search(request)
    search.append_filter(TopLevelAnnotationsFilter())
    for agg in aggregations_for(query):
        search.append_aggregation(agg)

    search_result = search.run(query)
    result = ActivityResults(total=search_result.total,
                             aggregations=search_result.aggregations,
                             timeframes=[])

    if result.total == 0:
        return result

    # Load all referenced annotations from the database, bucket them, and add
    # the buckets to result.timeframes.
    anns = _fetch_annotations(request.db, search_result.annotation_ids)
    result.timeframes.extend(bucketing.bucket(anns))

    # Fetch all groups
    group_pubids = set([a.groupid
                        for t in result.timeframes
                        for b in t.document_buckets.values()
                        for a in b.annotations])
    groups = {g.pubid: g for g in _fetch_groups(request.db, group_pubids)}

    # Add group information to buckets and present annotations
    for timeframe in result.timeframes:
        for bucket in timeframe.document_buckets.values():
            for index, annotation in enumerate(bucket.annotations):
                bucket.annotations[index] = {
                    'annotation': presenters.AnnotationHTMLPresenter(annotation),
                    'group': groups.get(annotation.groupid)
                }

    return result


def aggregations_for(query):
    aggregations = [TagsAggregation(limit=10)]

    # Should we aggregate by user?
    include_users_aggregation = len(query.getall('group')) == 1
    if include_users_aggregation:
        aggregations.append(UsersAggregation(limit=10))

    return aggregations


def _fetch_annotations(session, ids):
    return (session.query(Annotation)
            .options(subqueryload(Annotation.document)
                     .subqueryload(Document.meta_titles))
            .filter(Annotation.id.in_(ids))
            .order_by(Annotation.updated.desc()))


def _fetch_groups(session, pubids):
    return session.query(Group).filter(Group.pubid.in_(pubids))
