# -*- coding: utf-8 -*-

import logging

from elasticsearch import helpers
import webob.multidict

from h.api import models
from h.api.search import query

log = logging.getLogger(__name__)


def search(request_params, user=None, search_normalised_uris=False):
    """
    Search with the given params and return the matching annotations.

    :param request_params: the HTTP request params that were posted to the
        h search API
    :type request_params: webob.multidict.NestedMultiDict

    :param user: the authorized user, or None
    :type user: h.accounts.models.User or None

    :param search_normalised_uris: Whether or not to use the "uri" param to
        search against pre-normalised URI fields.
    :type search_normalised_uris: bool

    :returns: a dict with keys "rows" (the list of matching annotations, as
        dicts) and "total" (the number of matching annotations, an int)
    :rtype: dict
    """
    userid = user.id if user else None
    log.debug("Searching with user=%s, for uri=%s",
              str(userid), request_params.get('uri'))

    body = query.build(request_params,
                       userid=userid,
                       search_normalised_uris=search_normalised_uris)
    results = models.Annotation.search_raw(body, user=user, raw_result=True)

    total = results['hits']['total']
    docs = results['hits']['hits']
    rows = [models.Annotation(d['_source'], id=d['_id']) for d in docs]

    return {"rows": rows, "total": total}


def index(user=None, search_normalised_uris=False):
    """
    Return the 20 most recent annotations, most-recent first.

    Returns the 20 most recent annotations that are visible to the given user,
    or that are public if user is None.
    """
    return search(webob.multidict.NestedMultiDict({"limit": 20}),
                  user=user,
                  search_normalised_uris=search_normalised_uris)
