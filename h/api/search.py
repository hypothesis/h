"""The h API search functions.

All search (Annotation.search(), Annotation.search_raw()) and Elasticsearch
stuff should be encapsulated in this module.

"""
import copy
import logging

import elasticsearch
from elasticsearch import helpers
import webob.multidict

from h.api import models
from h.api import uri
from h.api import nipsa

log = logging.getLogger(__name__)


def _match_clause_for_uri(uristr):
    """Return an Elasticsearch match clause dict for the given URI."""
    if not uristr:
        return None

    uristrs = uri.expand(uri.normalise(uristr))
    matchers = [{"match": {"uri": uri.normalise(u)}} for u in uristrs]
    if len(matchers) == 1:
        return matchers[0]
    return {
        "bool": {
            "minimum_should_match": 1,
            "should": matchers
        }
    }


def scan(es_client, query, fields):
    return helpers.scan(es_client, query=query, fields=fields)


def bulk(es_client, actions):
    return helpers.bulk(es_client, actions)


def build_query(request_params, userid=None):
    """Return an Elasticsearch query dict for the given h search API params.

    Translates the HTTP request params accepted by the h search API into an
    Elasticsearch query dict.

    :param request_params: the HTTP request params that were posted to the
        h search API
    :type request_params: webob.multidict.NestedMultiDict

    :param userid: the ID of the authorized user (optional, default: None),
        if a userid is given then this user's annotations will never be
        filtered out even if they have a NIPSA flag
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

    return nipsa.nipsa_filter(query, userid=userid)


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
    userid = user.id if user else None
    log.debug("Searching with user=%s, for uri=%s",
              str(userid), request_params.get('uri'))

    query = build_query(request_params, userid=userid)
    results = models.Annotation.search_raw(query, user=user, raw_result=True)

    total = results['hits']['total']
    docs = results['hits']['hits']
    rows = [models.Annotation(d['_source'], id=d['_id']) for d in docs]

    return {"rows": rows, "total": total}


def index(user=None):
    """Return the 20 most recent annotations, most-recent first.

    Returns the 20 most recent annotations that are visible to the given user,
    or that are public if user is None.

    """
    return search(webob.multidict.NestedMultiDict({"limit": 20}), user=user)


def includeme(config):
    """Add a ``request.es_client`` property to the request."""
    es_host = config.registry.settings.get('es.host')
    if es_host:
        es_client = elasticsearch.Elasticsearch([es_host])
    else:
        es_client = elasticsearch.Elasticsearch()
    config.add_request_method(
        lambda _: es_client, 'es_client', reify=True)
