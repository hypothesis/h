# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from h import storage
from h.util import uri

LIMIT_DEFAULT = 20
LIMIT_MAX = 200


class Builder(object):

    """
    Build a query for execution in Elasticsearch.
    """

    def __init__(self):
        self.filters = []
        self.matchers = []
        self.aggregations = []

    def append_filter(self, f):
        self.filters.append(f)

    def append_matcher(self, m):
        self.matchers.append(m)

    def append_aggregation(self, a):
        self.aggregations.append(a)

    def build(self, params):
        """Get the resulting query object from this query builder."""
        params = params.copy()

        p_from = extract_offset(params)
        p_size = extract_limit(params)
        p_sort = extract_sort(params)

        filters = [f(params) for f in self.filters]
        matchers = [m(params) for m in self.matchers]
        aggregations = {a.key: a(params) for a in self.aggregations}
        filters = [f for f in filters if f is not None]
        matchers = [m for m in matchers if m is not None]

        # Remaining parameters are added as straightforward key-value matchers
        for key, value in params.items():
            matchers.append({"match": {key: value}})

        query = {"match_all": {}}

        if matchers:
            query = {"bool": {"must": matchers}}

        if filters:
            query = {"filtered": {"filter": {"and": filters}, "query": query}}

        return {
            "from": p_from,
            "size": p_size,
            "sort": p_sort,
            "query": query,
            "aggs": aggregations,
        }


def extract_offset(params):
    try:
        val = int(params.pop("offset"))
        if val < 0:
            raise ValueError
    except (ValueError, KeyError):
        return 0
    else:
        return val


def extract_limit(params):
    try:
        val = int(params.pop("limit"))
        val = min(val, LIMIT_MAX)
        if val < 0:
            raise ValueError
    except (ValueError, KeyError):
        return LIMIT_DEFAULT
    else:
        return val


def extract_sort(params):
    return [
        {
            params.pop("sort", "updated"): {
                "ignore_unmapped": True,
                "order": params.pop("order", "desc"),
            }
        }
    ]


class TopLevelAnnotationsFilter(object):

    """Matches top-level annotations only, filters out replies."""

    def __call__(self, _):
        return {"missing": {"field": "references"}}


class AuthorityFilter(object):

    """
    Match only annotations created by users belonging to a specific authority.
    """

    def __init__(self, authority):
        self.authority = authority

    def __call__(self, params):
        return {"term": {"authority": self.authority}}


class AuthFilter(object):

    """
    A filter that selects only annotations the user is authorised to see.

    Only annotations that are shared, or private annotations made
    by the logged-in user will pass through this filter.
    """

    def __init__(self, request):
        """
        Initialize a new AuthFilter.

        :param request: the pyramid.request object
        """
        self.request = request

    def __call__(self, params):
        public_filter = {"term": {"shared": True}}

        userid = self.request.authenticated_userid
        if userid is None:
            return public_filter

        return {"or": [public_filter, {"term": {"user_raw": userid}}]}


class GroupFilter(object):

    """
    Matches only those annotations belonging to the specified group.
    """

    def __call__(self, params):
        # Remove parameter if passed, preventing fall-through to default query
        group = params.pop("group", None)

        if group is not None:
            return {"term": {"group": group}}


class GroupAuthFilter(object):
    """Filter out groups that the request isn't authorized to read."""

    def __init__(self, request):
        self.user = request.user
        self.group_service = request.find_service(name="group")

    def __call__(self, _):
        groups = self.group_service.groupids_readable_by(self.user)
        return {"terms": {"group": groups}}


class UriFilter(object):

    """
    A filter that selects only annotations where the 'uri' parameter matches.
    """

    def __init__(self, request):
        """Initialize a new UriFilter.

        :param request: the pyramid.request object

        """
        self.request = request

    def __call__(self, params):
        if "uri" not in params and "url" not in params:
            return None
        query_uris = [v for k, v in params.items() if k in ["uri", "url"]]
        if "uri" in params:
            del params["uri"]
        if "url" in params:
            del params["url"]

        uris = set()
        for query_uri in query_uris:
            expanded = storage.expand_uri(self.request.db, query_uri)

            us = [uri.normalize(u) for u in expanded]
            uris.update(us)

        return {"terms": {"target.scope": list(uris)}}


class UserFilter(object):

    """
    A filter that selects only annotations where the 'user' parameter matches.
    """

    def __call__(self, params):
        if "user" not in params:
            return None

        users = [v.lower() for k, v in params.items() if k == "user"]
        del params["user"]

        return {"terms": {"user": users}}


class DeletedFilter(object):

    """
    A filter that only returns non-deleted documents.

    Documents are not getting deleted from the index, they only get marked as
    deleted.
    """

    def __call__(self, _):
        return {"bool": {"must_not": {"exists": {"field": "deleted"}}}}


class NipsaFilter(object):
    def __init__(self, request):
        self.group_service = request.find_service(name="group")
        self.user = request.user

    def __call__(self, _):
        return nipsa_filter(self.group_service, self.user)


def nipsa_filter(group_service, user=None):
    """Return an Elasticsearch filter for filtering out NIPSA'd annotations.

    The returned filter is suitable for inserting into an Es query dict.
    For example:

        query = {
            "query": {
                "filtered": {
                    "filter": nipsa_filter(),
                    "query": {...}
                }
            }
        }

    :param user: The user whose annotations should not be filtered.
        The returned filtered query won't filter out this user's annotations,
        even if the annotations have the NIPSA flag.
    :type user: h.models.User
    """
    # If any one of these "should" clauses is true then the annotation will
    # get through the filter.
    should_clauses = [
        {"not": {"term": {"nipsa": True}}},
        {"exists": {"field": "thread_ids"}},
    ]

    if user is not None:
        # Always show the logged-in user's annotations even if they have nipsa.
        should_clauses.append({"term": {"user": user.userid.lower()}})

        # Also include nipsa'd annotations for groups that the user created.
        created_groups = group_service.groupids_created_by(user)
        if created_groups:
            should_clauses.append({"terms": {"group": created_groups}})

    return {"bool": {"should": should_clauses}}


class AnyMatcher(object):

    """
    Matches the contents of a selection of fields against the `any` parameter.
    """

    def __call__(self, params):
        if "any" not in params:
            return None
        qs = " ".join([v for k, v in params.items() if k == "any"])
        result = {
            "simple_query_string": {
                "fields": ["quote", "tags", "text", "uri.parts"],
                "query": qs,
            }
        }
        del params["any"]
        return result


class TagsMatcher(object):

    """Matches the tags field against 'tag' or 'tags' parameters."""

    def __call__(self, params):
        tags = set(v for k, v in params.items() if k in ["tag", "tags"])
        try:
            del params["tag"]
            del params["tags"]
        except KeyError:
            pass
        matchers = [{"match": {"tags": {"query": t, "operator": "and"}}} for t in tags]
        return {"bool": {"must": matchers}} if matchers else None


class RepliesMatcher(object):

    """Matches any replies to any of the given annotation ids."""

    def __init__(self, ids):
        self.annotation_ids = ids

    def __call__(self, _):
        return {"terms": {"references": self.annotation_ids}}


class TagsAggregation(object):
    def __init__(self, limit=0):
        self.key = "tags"
        self.limit = limit

    def __call__(self, _):
        return {"terms": {"field": "tags_raw", "size": self.limit}}

    def parse_result(self, result):
        if not result:
            return {}

        return [{"tag": b["key"], "count": b["doc_count"]} for b in result["buckets"]]


class UsersAggregation(object):
    def __init__(self, limit=0):
        self.key = "users"
        self.limit = limit

    def __call__(self, _):
        return {"terms": {"field": "user_raw", "size": self.limit}}

    def parse_result(self, result):
        if not result:
            return {}

        return [{"user": b["key"], "count": b["doc_count"]} for b in result["buckets"]]
