# -*- coding: utf-8 -*-

import logging

import webob.multidict

from h.api import models
from h.api.search import query

log = logging.getLogger(__name__)


def search(request_params, user=None, search_normalized_uris=False):
    """
    Search with the given params and return the matching annotations.

    :param request_params: the HTTP request params that were posted to the
        h search API
    :type request_params: webob.multidict.NestedMultiDict

    :param user: the authorized user, or None
    :type user: h.accounts.models.User or None

    :param search_normalized_uris: Whether or not to use the "uri" param to
        search against pre-normalized URI fields.
    :type search_normalized_uris: bool

    :returns: a dict with keys:
        - "rows": The list of matching annotations, as dicts.
                  Note: only top-level annotations are returned here, not
                  reply annotations.
        - "total": The number of matching top-level annotations, an int.
        - "replies": The list of all reply annotations to the matching
                     top-level annotations, as dicts.
    :rtype: dict

    """
    userid = user.id if user else None
    log.debug("Searching with user=%s, for uri=%s",
              str(userid), request_params.get('uri'))

    body = query.build(request_params,
                       userid=userid,
                       search_normalized_uris=search_normalized_uris)
    results = models.Annotation.search_raw(body, user=user, raw_result=True)

    ids = [h['_id'] for h in results['hits']['hits']]
    replies = models.Annotation.search_raw(
        {
            'query': {
                'terms': {'references': ids}
            },
            'size': 10000,
        }, user=user, raw_result=True)

    if len(replies['hits']['hits']) < replies['hits']['total']:
        log.warn("The number of reply annotations exceeded the page size of "
                 "the Elasticsearch query. We currently don't handle this, "
                 "our search API doesn't support pagination of the reply set.")

    total = results['hits']['total']
    rows = [models.Annotation(hit['_source'], id=hit['_id'])
            for hit in results['hits']['hits']]
    replies = [models.Annotation(hit['_source'], id=hit['_id'])
               for hit in replies['hits']['hits']]

    return {"rows": rows, "total": total, "replies": replies}


def index(user=None, search_normalized_uris=False):
    """
    Return the 20 most recent annotations, most-recent first.

    Returns the 20 most recent annotations that are visible to the given user,
    or that are public if user is None.
    """
    return search(webob.multidict.NestedMultiDict({"limit": 20}),
                  user=user,
                  search_normalized_uris=search_normalized_uris)
