# -*- coding: utf-8 -*-
import logging

from h.api import models
from h.api import nipsa
from h.api.search import query


log = logging.getLogger(__name__)


def search(request, params, private=True):
    """
    Search with the given params and return the matching annotations.

    :param request: the request object
    :type request: pyramid.request.Request

    :param params: the search parameters
    :type params: dict-like

    :param private: whether or not to include private annotations in the search
        results
    :type private: bool

    :returns: a dict with keys "rows" (the list of matching annotations, as
        dicts) and "total" (the number of matching annotations, an int)
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
    builder.append_filter(query.TopLevelAnnotationsFilter())
    results = models.Annotation.search_raw(builder.build(params),
                                           raw_result=True,
                                           authorization_enabled=False)

    # Do a second query for all replies to the annotations from the first
    # query.
    builder = make_builder()
    builder.append_matcher(query.RepliesMatcher(
        [h['_id'] for h in results['hits']['hits']]))
    reply_results = models.Annotation.search_raw(builder.build({'limit': 100}),
                                                 raw_result=True,
                                                 authorization_enabled=False)

    if len(reply_results['hits']['hits']) < reply_results['hits']['total']:
        log.warn("The number of reply annotations exceeded the page size of "
                 "the Elasticsearch query. We currently don't handle this, "
                 "our search API doesn't support pagination of the reply set.")

    total = results['hits']['total']
    docs = results['hits']['hits']
    rows = [models.Annotation(d['_source'], id=d['_id']) for d in docs]
    reply_docs = reply_results['hits']['hits']
    reply_rows = [models.Annotation(d['_source'], id=d['_id'])
                  for d in reply_docs]

    return {"rows": rows, "total": total, "replies": reply_rows}
