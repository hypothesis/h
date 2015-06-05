"""The h API search functions.

All search and Elasticsearch stuff should be encapsulated in this module.

"""
import logging

from h.api.models import Annotation

log = logging.getLogger(__name__)


def _query(request_params):
    """Return an Elasticsearch query dict for the given h search API params.

    Translates the HTTP request params accepted by the h search API into an
    Elasticsearch query dict.

    :param request_params: the HTTP request params that were posted to the
        h search API
    :type request_params: webob.multidict.NestedMultiDict

    :returns: an Elasticsearch query dict corresponding to the given h search
        API params
    :rtype: dict

    """
    # NestedMultiDict objects are read-only, so we need to copy to make it
    # modifiable.
    request_params = request_params.copy()

    try:
        from_ = int(request_params.pop("offset"))
    except (ValueError, KeyError):
        from_ = 0

    try:
        size = int(request_params.pop("limit"))
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

    return query


def search(request_params, user=None):
    """Search with the given params and return the matching annotations.

    :param request_params: the HTTP request params that were posted to the
        h search API
    :type request_params: webob.multidict.NestedMultiDict

    :param user: the authorized user, or None
    :type user: h.accounts.models.User or None

    :returns: a dict with keys "rows" (the list of matching annotations, as
        dicts) and "total" (the number of matching annotations, an int)
    :rtype: dict

    """
    log.debug("Searching with user=%s, for uri=%s",
              user.id if user else 'None',
              request_params.get('uri'))

    query = _query(request_params)
    results = Annotation.search_raw(query, user=user)
    count = Annotation.search_raw(query, {'search_type': 'count'},
                                  raw_result=True)
    return {"rows": results, "total": count["hits"]["total"]}
