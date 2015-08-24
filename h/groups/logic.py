# -*- coding: utf-8 -*-
def url_for_group(request, group):
    """Return the URL for the given group's page."""
    hashid = group.hashid(request.hashids)
    return request.route_url('group_read', hashid=hashid, slug=group.slug)


def as_dict(request, group):
    """Return a JSON-serializable dict representation of this group."""
    group_dict = group.as_dict(request.hashids)
    group_dict['url'] = url_for_group(request, group)
    return group_dict
