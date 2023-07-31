import logging
from collections import namedtuple

import elasticsearch_dsl
from webob.multidict import MultiDict

from h.search import query
from h.util import metrics

log = logging.getLogger(__name__)

SearchResult = namedtuple(
    "SearchResult", ["total", "annotation_ids", "reply_ids", "aggregations"]
)


class Search:
    """
    Search is the primary way to initiate a search on the annotation index.

    :param request: the request object
    :type request: pyramid.request.Request

    :param separate_replies: Whether or not to return all replies to the
        annotations returned by this search. If this is True then the
        resulting annotations will only include top-level annotations, not replies.
    :type separate_replies: bool

    :param separate_wildcard_uri_keys: If True, wildcard searches are only performed
        on wildcard_uri's, and exact match searches are performed on uri/url parameters.
        If False, uri/url parameters are expected to contain both wildcard and exact
        matches.
    :type separate_wildcard_uri_keys: bool
    """

    def __init__(
        self,
        request,
        separate_replies=False,
        separate_wildcard_uri_keys=True,
        _replies_limit=200,
    ):
        self.es = request.es
        self.separate_replies = separate_replies
        self._replies_limit = _replies_limit
        # Order matters! The KeyValueMatcher must be run last,
        # after all other modifiers have popped off the params.
        self._modifiers = [
            query.Sorter(),
            query.Limiter(),
            query.DeletedFilter(),
            query.AuthFilter(request),
            query.GroupFilter(request),
            query.UserFilter(),
            query.HiddenFilter(request),
            query.AnyMatcher(),
            query.TagsMatcher(),
            query.UriCombinedWildcardFilter(
                request, separate_keys=separate_wildcard_uri_keys
            ),
            query.KeyValueMatcher(),
        ]
        self._aggregations = []

    def run(self, params):
        """
        Execute the search query.

        :param params: the search parameters that will be popped by each of the filters.
        :type params: webob.multidict.MultiDict

        :returns: The search results
        :rtype: SearchResult
        """
        metrics.record_search_query_params(params, self.separate_replies)
        total, annotation_ids, aggregations = self._search_annotations(params)
        reply_ids = self._search_replies(annotation_ids)

        return SearchResult(total, annotation_ids, reply_ids, aggregations)

    def clear(self):
        """Clear search modifiers, aggregators, and matchers."""
        self._modifiers = [query.Sorter()]
        self._aggregations = []

    def append_modifier(self, modifier):
        """Append a search modifier, matcher, etc to the search query."""
        # Note we must insert any new modifier at the begining of the list
        # since the KeyValueFilter must always be run after all the other
        # modifiers.
        self._modifiers.insert(0, modifier)

    def append_aggregation(self, aggregation):
        """Append an aggregation to the search query."""
        self._aggregations.append(aggregation)

    def _search(self, modifiers, aggregations, params):
        """Apply the modifiers, aggregations, and executes the search."""
        # Don't return any fields, just the metadata so set _source=False.
        search = elasticsearch_dsl.Search(
            using=self.es.conn, index=self.es.index
        ).source(False)

        for agg in aggregations:
            agg(search, params)
        for qual in modifiers:
            search = qual(search, params)

        return search.execute()

    def _search_annotations(self, params):
        # If separate_replies is True, don't return any replies to annotations.
        modifiers = self._modifiers
        if self.separate_replies:
            modifiers = [query.TopLevelAnnotationsFilter()] + modifiers

        response = self._search(modifiers, self._aggregations, params)

        total = self._get_total_hits(response)
        annotation_ids = [hit["_id"] for hit in response["hits"]["hits"]]
        aggregations = self._parse_aggregation_results(response.aggregations)
        return (total, annotation_ids, aggregations)

    def _search_replies(self, annotation_ids):
        if not self.separate_replies:
            return []

        # The only difference between a search for annotations and a search for
        # replies to annotations is the RepliesMatcher and the params passed to
        # the modifiers.
        response = self._search(
            [query.RepliesMatcher(annotation_ids)] + self._modifiers,
            [],  # Aggregations aren't used in replies.
            MultiDict({"limit": self._replies_limit}),
        )

        if len(response["hits"]["hits"]) < self._get_total_hits(response):
            log.warning(
                "The number of reply annotations exceeded the page size "
                "of the Elasticsearch query. We currently don't handle "
                "this, our search API doesn't support pagination of the "
                "reply set."
            )

        return [hit["_id"] for hit in response["hits"]["hits"]]

    def _parse_aggregation_results(self, aggregations):
        if not aggregations:
            return {}

        results = {}
        for agg in self._aggregations:
            results[agg.name] = agg.parse_result(aggregations)
        return results

    @staticmethod
    def _get_total_hits(response):
        total = response["hits"]["total"]
        if isinstance(total, int):
            # ES 6.x
            return total

        # ES 7.x
        return total["value"]  # pragma: nocover
