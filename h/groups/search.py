# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models import Group
from h.models.group import ReadableBy


class GroupAuthFilter(object):
    """
    A memex search filter that filters out groups the request isn't authorized to read.
    """

    def __init__(self, request):
        self.authenticated_user = request.authenticated_user
        self.session = request.db

    def __call__(self, _):
        groups = set(['__world__'])

        if self.authenticated_user:
            for group in self.authenticated_user.groups:
                groups.add(group.pubid)

        world_readable_groups = self.session.query(Group.pubid).filter_by(readable_by=ReadableBy.world)
        for group in world_readable_groups:
            groups.add(group[0])

        return {'terms': {'group': list(groups)}}
