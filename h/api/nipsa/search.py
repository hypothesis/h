# -*- coding: utf-8 -*-
def nipsa_filter(userid=None):
    """Return an Elasticsearch filter for filtering out NIPSA'd annotations.

    The returned filter is suitable for inserting into an Es query dict.
    For example:

        query = {
            "query": {
                "filtered": {
                    "filter": nipsa_filter(),
                    "query": {...}
                }
            }
        }

    :param userid: The ID of a user whose annotations should not be filtered.
        The returned filtered query won't filter out this user's annotations,
        even if the annotations have the NIPSA flag.
    :type userid: unicode

    """
    # If any one of these "should" clauses is true then the annotation will
    # get through the filter.
    should_clauses = [{"not": {"term": {"nipsa": True}}}]

    if userid is not None:
        # Always show the logged-in user's annotations even if they have nipsa.
        should_clauses.append({"term": {"user": userid}})

    return {"bool": {"should": should_clauses}}


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
        {"term": {"nipsa": True}})
    return query


def not_nipsad_annotations(userid):
    """Return an Elasticsearch query for the user's non-NIPSA'd annotations."""
    query = query_for_users_annotations(userid)
    query["query"]["filtered"]["filter"]["bool"]["must"].append(
        {"not": {"term": {"nipsa": True}}})
    return query
