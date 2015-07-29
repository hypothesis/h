from h.api import uri
from h.api import nipsa


def build(request_params, userid=None):
    """
    Return an Elasticsearch query dict for the given h search API params.

    Translates the HTTP request params accepted by the h search API into an
    Elasticsearch query dict.

    :param request_params: the HTTP request params that were posted to the
        h search API
    :type request_params: webob.multidict.NestedMultiDict

    :param userid: the ID of the authorized user (optional, default: None),
    :type userid: unicode or None

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

    query = {
        "from": from_,
        "size": size,
        "sort": [
            {
                request_params.pop("sort", "updated"): {
                    "ignore_unmapped": True,
                    "order": request_params.pop("order", "desc")
                }
            }
        ]
    }

    matches = []
    uri_match_clause = _match_clause_for_uri(request_params.pop("uri", None))
    if uri_match_clause:
        matches.append(uri_match_clause)

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
    matches = matches or [{"match_all": {}}]

    query["query"] = {"bool": {"must": matches}}

    query["query"] = {
        "filtered": {
            "filter": nipsa.nipsa_filter(userid=userid),
            "query": query["query"]
        }
    }

    return query


def _match_clause_for_uri(uristr):
    """Return an Elasticsearch match clause dict for the given URI."""
    if not uristr:
        return None

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
