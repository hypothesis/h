# -*- coding: utf-8 -*-
from h.api import uri


class Builder(object):

    """
    Build a query for execution in Elasticsearch.
    """

    def __init__(self):
        self.filters = []
        self.matchers = []

    def append_filter(self, f):
        self.filters.append(f)

    def append_matcher(self, m):
        self.matchers.append(m)

    def build(self, params):
        """Get the resulting query object from this query builder."""
        params = params.copy()

        p_from = extract_offset(params)
        p_size = extract_limit(params)
        p_sort = extract_sort(params)

        filters = [f(params) for f in self.filters]
        matchers = [m(params) for m in self.matchers]
        filters = [f for f in filters if f is not None]
        matchers = [m for m in matchers if m is not None]

        # Remaining parameters are added as straightforward key-value matchers
        for key, value in params.items():
            matchers.append({"match": {key: value}})

        query = {"match_all": {}}

        if matchers:
            query = {"bool": {"must": matchers}}

        if filters:
            query = {
                "filtered": {
                    "filter": {"and": filters},
                    "query": query,
                }
            }

        return {
            "from": p_from,
            "size": p_size,
            "sort": p_sort,
            "query": query,
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
        if val < 0:
            raise ValueError
    except (ValueError, KeyError):
        return 20
    else:
        return val


def extract_sort(params):
    return [{
        params.pop("sort", "updated"): {
            "ignore_unmapped": True,
            "order": params.pop("order", "desc"),
        }
    }]


class AuthFilter(object):

    """
    A filter that selects only annotations the user is authorised to see.

    Only annotations where the 'read' permission contains one or more of the
    user's effective principals will pass through this filter.
    """

    def __init__(self, request, private=True):
        """Initialize a new AuthFilter.

        :param request: the pyramid.request object

        :param private: whether or not to include private annotations in the
            search results
        :type private: bool

        """
        self.request = request
        self.private = private

    def __call__(self, params):
        principals = list(self.request.effective_principals)

        # We always want annotations with 'group:__world__' in their read
        # permissions to show up in the search results, but 'group:__world__'
        # is not in effective_principals for unauthenticated requests.
        #
        # FIXME: If public annotations used 'system.Everyone'
        # instead of 'group:__world__' we wouldn't have to do this.
        if 'group:__world__' not in principals:
            principals.insert(0, 'group:__world__')

        if not self.private:
            principals = [p for p in principals
                          if not p == self.request.authenticated_userid]

        return {'terms': {'permissions.read': principals}}


class GroupFilter(object):

    """
    Matches only those annotations belonging to the specified group.

    When the groups feature flag is off, this ensures that only annotations
    from the public group are returned.
    """

    def __init__(self, request):
        self.request = request

    def __call__(self, params):
        # Remove parameter if passed, preventing fall-through to default query
        group = params.pop("group", None)

        if not self.request.feature('groups'):
            return {"term": {"group": "__world__"}}

        if group is not None:
            return {"term": {"group": group}}


class UriFilter(object):

    """
    A filter that selects only annotations where the 'uri' parameter matches.
    """

    def __call__(self, params):
        uristr = params.pop('uri', None)
        if uristr is None:
            return None

        scopes = [uri.normalize(u) for u in uri.expand(uristr)]
        return {"terms": {"target.scope": scopes}}


class AnyMatcher(object):

    """
    Matches the contents of a selection of fields against the `any` parameter.
    """

    def __call__(self, params):
        if "any" not in params:
            return None
        qs = ' '.join([v for k, v in params.items() if k == "any"])
        result = {
            "simple_query_string": {
                "fields": ["quote", "tags", "text", "uri.parts", "user"],
                "query": qs,
            }
        }
        del params["any"]
        return result


class TagsMatcher(object):

    """Matches the tags field against 'tag' or 'tags' parameters."""

    def __call__(self, params):
        tags = set(v for k, v in params.items() if k in ['tag', 'tags'])
        try:
            del params['tag']
            del params['tags']
        except KeyError:
            pass
        matchers = [{'match': {'tags': {'query': t, 'operator': 'and'}}}
                    for t in tags]
        return {'bool': {'must': matchers}} if matchers else None
