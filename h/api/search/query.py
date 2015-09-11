# -*- coding: utf-8 -*-
from h.api import nipsa
from h.api import uri


def auth_filter(effective_principals):
    """Return an Elasticsearch filter for authorized annotations.

    Only annotations that the given effective_principals are authorized to
    read will pass through this filter.

    """
    groups = list(effective_principals)

    # We always want annotations with 'group:__world__' in
    # their read permissions to show up in the search results,
    # but 'group:__world__' is not in effective_principals for unauthenticed
    # requests.
    # FIXME: If public annotations used 'system.Everyone'
    # instead of 'group:__world__' we wouldn't have to do this.
    if 'group:__world__' not in groups:
        groups.insert(0, 'group:__world__')

    return {'terms': {'permissions.read': groups}}


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

    filters = [auth_filter(effective_principals)]
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
    filters = [{"term": {"target.scope": uri.normalize(u)}}
               for u in uristrs]

    if len(filters) == 1:
        return filters[0]
    return {
        "or": filters
    }
