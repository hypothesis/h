# -*- coding: utf-8 -*-
import logging
from collections import namedtuple

from h.api.search import query

FILTERS_KEY = 'h.api.search.filters'
MATCHERS_KEY = 'h.api.search.matchers'

log = logging.getLogger(__name__)

SearchResult = namedtuple('SearchResult', [
    'total',
    'annotation_ids',
    'reply_ids'])


def search(request, params, private=True, separate_replies=False):
    """
    Search with the given params and return the matching annotations.

    :param request: the request object
    :type request: pyramid.request.Request

    :param params: the search parameters
    :type params: dict-like

    :param private: whether or not to include private annotations in the search
        results
    :type private: bool

    :param separate_replies: Whether or not to include a "replies" key in the
        result containing a list of all replies to the annotations in the
        "rows" key. If this is True then the "rows" key will include only
        top-level annotations, not replies.
    :type private: bool

    :returns: A dict with keys:
      "rows" (the list of matching annotations, as dicts)
      "total" (the number of matching annotations, an int)
      "replies": (the list of all replies to the annotations in "rows", if
        separate_replies=True was passed)
    :rtype: dict
    """
    builder = default_querybuilder(request, private=private)
    if separate_replies:
        builder.append_filter(query.TopLevelAnnotationsFilter())

    es = request.es
    response = es.conn.search(index=es.index,
                              doc_type=es.t.annotation,
                              body=builder.build(params))
    total = response['hits']['total']
    annotation_ids = [hit['_id'] for hit in response['hits']['hits']]
    reply_ids = []

    if separate_replies:
        # Do a second query for all replies to the annotations from the first
        # query.
        builder = default_querybuilder(request, private=private)
        builder.append_matcher(query.RepliesMatcher(annotation_ids))
        reply_response = es.conn.search(index=es.index,
                                        doc_type=es.t.annotation,
                                        body=builder.build({'limit': 200}))

        if len(reply_response['hits']['hits']) < reply_response['hits']['total']:
            log.warn("The number of reply annotations exceeded the page size "
                     "of the Elasticsearch query. We currently don't handle "
                     "this, our search API doesn't support pagination of the "
                     "reply set.")

        reply_ids = [hit['_id'] for hit in reply_response['hits']['hits']]

    return SearchResult(total, annotation_ids, reply_ids)


def default_querybuilder(request, private=True):
    builder = query.Builder()
    builder.append_filter(query.AuthFilter(request, private=private))
    builder.append_filter(query.UriFilter(request))
    builder.append_filter(query.GroupFilter())
    builder.append_filter(query.UserFilter())
    builder.append_matcher(query.AnyMatcher())
    builder.append_matcher(query.TagsMatcher())
    for factory in request.registry.get(FILTERS_KEY, []):
        builder.append_filter(factory(request))
    for factory in request.registry.get(MATCHERS_KEY, []):
        builder.append_matcher(factory(request))
    return builder
