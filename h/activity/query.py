# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import namedtuple

import newrelic.agent
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.orm import subqueryload

from h import links
from h import presenters
from h import storage
from h.activity import bucketing
from h.models import Annotation, Group
from h.search import Search
from h.search import parser
from h.search.query import (
    AuthorityFilter,
    TagsAggregation,
    TopLevelAnnotationsFilter,
    UsersAggregation,
)


class ActivityResults(namedtuple('ActivityResults', [
    'total',
    'aggregations',
    'timeframes',
])):
    pass


@newrelic.agent.function_trace()
def extract(request, parse=parser.parse):
    """
    Extract and process the query present in the passed request.

    Assumes that the 'q' query parameter contains a string query in a format
    which can be parsed by :py:func:`h.search.parser.parse`. Extracts and
    parses the query, adds terms implied by the current matched route, if
    necessary, and returns it.

    If no query is present in the passed request, returns ``None``.
    """

    q = parse(request.params.get('q', ''))

    # If the query sent to a {group, user} search page includes a {group,
    # user}, we override it, because otherwise we'll display the union of the
    # results for those two {groups, users}, which would makes no sense.
    #
    # (Note that a query for the *intersection* of >1 users or groups is by
    # definition empty)
    if request.matched_route.name == 'group_read':
        q['group'] = request.matchdict['pubid']
    elif request.matched_route.name == 'activity.user_search':
        q['user'] = request.matchdict['username']

    return q


def check_url(request, query, unparse=parser.unparse):
    """
    Checks the request and raises a redirect if implied by the query.

    If a query contains a single group or user term, then the user is
    redirected to the specific group or user search page with that term
    removed. For example, a request to

        /search?q=group:abc123+tag:foo

    will be redirected to

        /groups/abc123/search?q=tag:foo

    Queries containing more than one group or user term are unaffected.
    """
    if request.matched_route.name != 'activity.search':
        return

    redirect = None

    if _single_entry(query, 'group'):
        pubid = query.pop('group')
        group = request.db.query(Group).filter_by(pubid=pubid).one_or_none()
        if group:
            redirect = request.route_path('group_read',
                                          pubid=group.pubid,
                                          slug=group.slug,
                                          _query={'q': unparse(query)})

    elif _single_entry(query, 'user'):
        username = query.pop('user')
        user = request.find_service(name='user').fetch(username,
                                                       request.authority)
        if user:
            redirect = request.route_path('activity.user_search',
                                          username=username,
                                          _query={'q': unparse(query)})

    if redirect is not None:
        raise HTTPFound(location=redirect)


@newrelic.agent.function_trace()
def execute(request, query, page_size):
    search_result = _execute_search(request, query, page_size)

    result = ActivityResults(total=search_result.total,
                             aggregations=search_result.aggregations,
                             timeframes=[])

    if result.total == 0:
        return result

    # Load all referenced annotations from the database, bucket them, and add
    # the buckets to result.timeframes.
    anns = fetch_annotations(request.db, search_result.annotation_ids)
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
            bucket.presented_annotations = []
            for annotation in bucket.annotations:
                bucket.presented_annotations.append({
                    'annotation': presenters.AnnotationHTMLPresenter(annotation),
                    'group': groups.get(annotation.groupid),
                    'html_link': links.html_link(request, annotation),
                    'incontext_link': links.incontext_link(request, annotation)
                })

    return result


def aggregations_for(query):
    aggregations = [TagsAggregation(limit=50)]

    # Should we aggregate by user?
    if _single_entry(query, 'group'):
        aggregations.append(UsersAggregation(limit=50))

    return aggregations


@newrelic.agent.function_trace()
def fetch_annotations(session, ids):
    def load_documents(query):
        return query.options(subqueryload(Annotation.document))

    annotations = storage.fetch_ordered_annotations(
        session, ids, query_processor=load_documents)

    return annotations


@newrelic.agent.function_trace()
def _execute_search(request, query, page_size):
    search = Search(request, stats=request.stats)
    search.append_filter(AuthorityFilter(authority=request.authority))
    search.append_filter(TopLevelAnnotationsFilter())
    for agg in aggregations_for(query):
        search.append_aggregation(agg)

    query = query.copy()
    page = request.params.get('page', 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    # Don't allow negative page numbers.
    if page < 1:
        page = 1

    query['limit'] = page_size
    query['offset'] = (page - 1) * page_size

    search_result = search.run(query)
    return search_result


@newrelic.agent.function_trace()
def _fetch_groups(session, pubids):
    return session.query(Group).filter(Group.pubid.in_(pubids))


def _single_entry(query, key):
    return len(query.getall(key)) == 1
