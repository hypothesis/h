# -*- coding: utf-8 -*-
from h import hashids


def url_for_group(request, group):
    """Return the URL for the given group's page."""
    hashid = hashids.encode(request, "h.groups", number=group.id)
    return request.route_url('group_read', hashid=hashid, slug=group.slug)
