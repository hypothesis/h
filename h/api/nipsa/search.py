import copy


def nipsa_filter(query, userid=None):
    """Return a NIPSA-filtered copy of the given query dict.

    Given an Elasticsearch query dict like this:

        query = {"query": {...}}

    return a filtered query dict like this:

        query = {
            "query": {
                "filtered": {
                    "filter": {...},
                    "query": <the original query>
                }
            }
        }

    where the filter is one that filters out all NIPSA'd annotations.

    Returns a new dict, doesn't modify the given dict.

    :param query: The query to return a filtered copy of
    :type query: dict

    :param userid: The ID of a user whose annotations should not be filtered.
        The returned filtered query won't filter out this user's annotations,
        even if the annotations have the NIPSA flag.
    :type userid: unicode

    """
    query = copy.deepcopy(query)

    # If any one of these "should" clauses is true then the annotation will
    # get through the filter.
    should_clauses = [{"not": {"term": {"not_in_public_site_areas": True}}}]

    if userid:
        # Always show the logged-in user's annotations even if they have nipsa.
        should_clauses.append({"term": {"user": userid}})

    query["query"] = {
        "filtered": {
            "filter": {"bool": {"should": should_clauses}},
            "query": query["query"]
        }
    }

    return query


def query_for_users_annotations(userid):
    """Return an Elasticsearch query for all the given user's annotations."""
    return {
        "query": {
            "filtered": {
                "filter": {
                    "bool": {
                        "must": [{"term": {"user": userid}}]
                    }
                }
            }
        }
    }


def nipsad_annotations(userid):
    """Return an Elasticsearch query for the user's NIPSA'd annotations."""
    query = query_for_users_annotations(userid)
    query["query"]["filtered"]["filter"]["bool"]["must"].append(
        {"term": {"not_in_public_site_areas": True}})
    return query


def not_nipsad_annotations(userid):
    """Return an Elasticsearch query for the user's non-NIPSA'd annotations."""
    query = query_for_users_annotations(userid)
    query["query"]["filtered"]["filter"]["bool"]["must"].append(
        {"not": {"term": {"not_in_public_site_areas": True}}})
    return query
