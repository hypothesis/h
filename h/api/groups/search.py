def group_filter(request):
    """Return an Elasticsearch filter for the given user's groups.

    This will filter out annotations that belong to groups that the given user
    isn't a member of. Annotations belonging to no group and annotations
    belonging to any group that the user is a member of, will pass through the
    filter.

    The returned filter is suitable for inserting into an Es query dict.
    For example:

        query = {
            "query": {
                "filtered": {
                    "filter": group_filter(),
                    "query": {...}
                }
            }
        }

    :param request: The Pyramid request object
    :type request: pyramid.request.Request

    """
    # Annotations that have no 'group' field or a null value for the group
    # field should pass through the filter.
    should_clauses = [{'missing': {'field': 'group'}}]

    # We always want group: '__none__' annotations to pass through the groups
    # search filter.
    hashids = ['__none__']

    # Annotations whose 'group' field's value matches one of the hashids in
    # the request's 'group:<hashid>' principals should pass through the filter.
    hashids.extend([p.split(':', 1)[1] for p in request.effective_principals
                    if p.startswith('group:')])

    if len(hashids) > 1:
        should_clauses.append({'terms': {'group': hashids}})
    else:
        should_clauses.append({'term': {'group': hashids[0]}})

    # Combining the should_clauses with a {'bool': {'should': [...]}}
    # filter means that if any one of the should clauses passes then the
    # annotation will pass through the filter.
    return {'bool': {'should': should_clauses}}
