# -*- coding: utf-8 -*-
from h.api import uri
from h.api import nipsa
from h.api import groups


def build(request_params, effective_principals, userid=None,
          search_normalized_uris=False):
    """
    Return an Elasticsearch query dict for the given h search API params.

    Translates the HTTP request params accepted by the h search API into an
    Elasticsearch query dict.

    :param request_params: the HTTP request params that were posted to the
        h search API
    :type request_params: webob.multidict.NestedMultiDict

    :param effective_principals: request.effective_principals

    :param userid: request.authenticated_userid

    :param search_normalized_uris: Whether or not to use the "uri" param to
        search against pre-normalized URI fields.
    :type search_normalized_uris: bool

    :returns: an Elasticsearch query dict corresponding to the given h search
        API params
    :rtype: dict
    """
    # NestedMultiDict objects are read-only, so we need to copy to make it
    # modifiable.
    request_params = request_params.copy()

    try:
        from_ = int(request_params.pop("offset"))
        if from_ < 0:
            raise ValueError
    except (ValueError, KeyError):
        from_ = 0

    try:
        size = int(request_params.pop("limit"))
        if size < 0:
            raise ValueError
    except (ValueError, KeyError):
        size = 20

    sort = [{
        request_params.pop("sort", "updated"): {
            "ignore_unmapped": True,
            "order": request_params.pop("order", "desc")
        }
    }]

    filters = []
    matches = []

    uri_param = request_params.pop("uri", None)
    if uri_param is None:
        pass
    elif search_normalized_uris:
        filters.append(_term_clause_for_uri(uri_param))
    else:
        matches.append(_match_clause_for_uri(uri_param))

    if "any" in request_params:
        matches.append({
            "multi_match": {
                "fields": ["quote", "tags", "text", "uri.parts", "user"],
                "query": request_params.getall("any"),
                "type": "cross_fields"
            }
        })
        del request_params["any"]

    for key, value in request_params.items():
        matches.append({"match": {key: value}})

    # Add a filter for "not in public site areas" considerations
    filters.append(nipsa.nipsa_filter(userid=userid))

    filters.append(groups.group_filter(effective_principals))

    query = {"match_all": {}}

    if matches:
        query = {"bool": {"must": matches}}

    if filters:
        query = {
            "filtered": {
                "filter": {"and": filters},
                "query": query,
            }
        }

    return {
        "from": from_,
        "size": size,
        "sort": sort,
        "query": query,
    }


def _match_clause_for_uri(uristr):
    """Return an Elasticsearch match clause dict for the given URI."""
    uristrs = uri.expand(uristr)
    matchers = [{"match": {"uri": u}} for u in uristrs]

    if len(matchers) == 1:
        return matchers[0]
    return {
        "bool": {
            "minimum_should_match": 1,
            "should": matchers
        }
    }


def _term_clause_for_uri(uristr):
    """Return an Elasticsearch term clause for the given URI."""
    uristrs = uri.expand(uristr)
    filters = [{"term": {"target.source_normalized": uri.normalize(u)}}
               for u in uristrs]

    if len(filters) == 1:
        return filters[0]
    return {
        "or": filters
    }
