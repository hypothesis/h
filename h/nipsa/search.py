# -*- coding: utf-8 -*-


class Filter(object):
    def __init__(self, request):
        self.group_service = request.find_service(name='group')
        self.user = request.user

    def __call__(self, _):
        return nipsa_filter(self.group_service, self.user)


def nipsa_filter(group_service, user=None):
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

    :param user: The user whose annotations should not be filtered.
        The returned filtered query won't filter out this user's annotations,
        even if the annotations have the NIPSA flag.
    :type user: h.models.User
    """
    # If any one of these "should" clauses is true then the annotation will
    # get through the filter.
    should_clauses = [
        {"bool": {"must_not": {"term": {"nipsa": True}}}},
        {"exists": {"field": "thread_ids"}},
    ]

    if user is not None:
        # Always show the logged-in user's annotations even if they have nipsa.
        should_clauses.append({"term": {"user": user.userid.lower()}})

        # Also include nipsa'd annotations for groups that the user created.
        created_groups = group_service.groupids_created_by(user)
        if created_groups:
            should_clauses.append({"terms": {"group": created_groups}})

    return {"bool": {"should": should_clauses}}
