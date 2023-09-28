from collections import namedtuple

import newrelic.agent
from pyramid.httpexceptions import HTTPFound

from h import links, presenters
from h.activity import bucketing
from h.models import Annotation, Group
from h.search import (
    AuthorityFilter,
    Search,
    TagsAggregation,
    TopLevelAnnotationsFilter,
    UsersAggregation,
    parser,
)
from h.services.annotation_read import AnnotationReadService


class ActivityResults(
    namedtuple("ActivityResults", ["total", "aggregations", "timeframes"])
):
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

    query = parse(request.params.get("q", ""))

    # If the query sent to a {group, user} search page includes a {group,
    # user}, we override it, because otherwise we'll display the union of the
    # results for those two {groups, users}, which would makes no sense.
    #
    # (Note that a query for the *intersection* of >1 users or groups is by
    # definition empty)
    if request.matched_route.name == "group_read":
        query["group"] = request.matchdict["pubid"]
    elif request.matched_route.name == "activity.user_search":
        query["user"] = request.matchdict["username"]

    return query


def check_url(request, query, unparse=parser.unparse):
    """
    Check the request and raises a redirect if implied by the query.

    If a query contains a single group or user term, then the user is
    redirected to the specific group or user search page with that term
    removed. For example, a request to

        /search?q=group:abc123+tag:foo

    will be redirected to

        /groups/abc123/search?q=tag:foo

    Queries containing more than one group or user term are unaffected.
    """
    if request.matched_route.name != "activity.search":
        return

    redirect = None

    if _single_entry(query, "group"):
        pubid = query.get("group")
        group = request.db.query(Group).filter_by(pubid=pubid).one_or_none()
        if group:
            query.pop("group")
            redirect = request.route_path(
                "group_read",
                pubid=group.pubid,
                slug=group.slug,
                _query={"q": unparse(query)},
            )

    elif _single_entry(query, "user"):
        username = query.get("user")
        user = request.find_service(name="user").fetch(
            username, request.default_authority
        )
        if user:
            query.pop("user")
            redirect = request.route_path(
                "activity.user_search", username=username, _query={"q": unparse(query)}
            )

    if redirect is not None:
        raise HTTPFound(location=redirect)


@newrelic.agent.function_trace()
def execute(request, query, page_size):
    search_result = _execute_search(request, query, page_size)

    result = ActivityResults(
        total=search_result.total,
        aggregations=search_result.aggregations,
        timeframes=[],
    )

    if not result.total:
        return result

    # Load all referenced annotations from the database, bucket them, and add
    # the buckets to result.timeframes.
    anns = _fetch_annotations(request, search_result.annotation_ids)
    result.timeframes.extend(bucketing.bucket(anns))

    # Fetch all groups
    group_pubids = {
        a.groupid
        for t in result.timeframes
        for b in t.document_buckets.values()
        for a in b.annotations
    }
    groups = {g.pubid: g for g in _fetch_groups(request.db, group_pubids)}

    # Add group information to buckets and present annotations
    for timeframe in result.timeframes:
        for bucket in timeframe.document_buckets.values():
            bucket.presented_annotations = []
            for annotation in bucket.annotations:
                bucket.presented_annotations.append(
                    {
                        "annotation": presenters.AnnotationHTMLPresenter(annotation),
                        "group": groups.get(annotation.groupid),
                        "html_link": links.html_link(request, annotation),
                        "incontext_link": links.incontext_link(request, annotation),
                    }
                )

    return result


def aggregations_for(query):
    aggregations = [TagsAggregation(limit=50)]

    # Should we aggregate by user?
    if _single_entry(query, "group"):
        aggregations.append(UsersAggregation(limit=50))

    return aggregations


@newrelic.agent.function_trace()
def _fetch_annotations(request, ids):
    return request.find_service(AnnotationReadService).get_annotations_by_id(
        ids=ids, eager_load=[Annotation.document]
    )


@newrelic.agent.function_trace()
def _execute_search(request, query, page_size):
    # Wildcards and exact url matches are specified in the url facet so set
    # separate_wildcard_uri_keys to False.
    search = Search(request, separate_wildcard_uri_keys=False)
    search.append_modifier(AuthorityFilter(authority=request.default_authority))
    search.append_modifier(TopLevelAnnotationsFilter())
    for agg in aggregations_for(query):
        search.append_aggregation(agg)

    query = query.copy()
    page = request.params.get("page", 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    # Don't allow negative page numbers.
    page = max(page, 1)

    query["limit"] = page_size
    query["offset"] = (page - 1) * page_size

    search_result = search.run(query)
    return search_result


@newrelic.agent.function_trace()
def _fetch_groups(session, pubids):  # pragma: no cover
    return session.query(Group).filter(Group.pubid.in_(pubids))


def _single_entry(query, key):
    return len(query.getall(key)) == 1
