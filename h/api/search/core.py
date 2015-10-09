# -*- coding: utf-8 -*-
from h.api import models
from h.api import nipsa
from h.api.search import query


def search(request, params):
    """
    Search with the given params and return the matching annotations.

    :param request: the request object
    :type request: pyramid.request.Request

    :param params: the search parameters
    :type params: dict-like

    :returns: a dict with keys "rows" (the list of matching annotations, as
        dicts) and "total" (the number of matching annotations, an int)
    :rtype: dict
    """
    builder = query.Builder()

    builder.append_filter(query.AuthFilter(request))
    builder.append_filter(query.UriFilter())
    builder.append_filter(lambda _: \
        nipsa.nipsa_filter(request.authenticated_userid))
    builder.append_filter(query.GroupFilter(request))

    builder.append_matcher(query.AnyMatcher())
    builder.append_matcher(query.TagsMatcher())

    body = builder.build(params)
    results = models.Annotation.search_raw(body,
                                           raw_result=True,
                                           authorization_enabled=False)

    total = results['hits']['total']
    docs = results['hits']['hits']
    rows = [models.Annotation(d['_source'], id=d['_id']) for d in docs]

    return {"rows": rows, "total": total}
