# -*- coding: utf-8 -*-
import logging

from h.api import nipsa
from h.api.search import query


log = logging.getLogger(__name__)


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
    def make_builder():
        builder = query.Builder()
        builder.append_filter(query.AuthFilter(request, private=private))
        builder.append_filter(query.UriFilter())
        builder.append_filter(
            lambda _: nipsa.nipsa_filter(request.authenticated_userid))
        builder.append_filter(query.GroupFilter())
        builder.append_matcher(query.AnyMatcher())
        builder.append_matcher(query.TagsMatcher())
        return builder

    builder = make_builder()
    if separate_replies:
        builder.append_filter(query.TopLevelAnnotationsFilter())

    es = request.es
    results = es.conn.search(index=es.index,
                             doc_type=es.t.annotation,
                             body=builder.build(params))
    total = results['hits']['total']
    docs = results['hits']['hits']
    rows = [dict(d['_source'], id=d['_id']) for d in docs]
    return_value = {"rows": rows, "total": total}

    if separate_replies:
        # Do a second query for all replies to the annotations from the first
        # query.
        builder = make_builder()
        builder.append_matcher(query.RepliesMatcher(
            [h['_id'] for h in results['hits']['hits']]))
        reply_results = es.conn.search(index=es.index,
                                       doc_type=es.t.annotation,
                                       body=builder.build({'limit': 100}))

        if len(reply_results['hits']['hits']) < reply_results['hits']['total']:
            log.warn("The number of reply annotations exceeded the page size "
                     "of the Elasticsearch query. We currently don't handle "
                     "this, our search API doesn't support pagination of the "
                     "reply set.")

        reply_docs = reply_results['hits']['hits']
        reply_rows = [dict(d['_source'], id=d['_id']) for d in reply_docs]

        return_value["replies"] = reply_rows

    return return_value
