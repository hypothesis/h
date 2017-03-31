# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class GroupAuthFilter(object):
    """
    A search filter that filters out groups the request isn't authorized to read.
    """

    def __init__(self, request):
        self.user = request.user
        self.session = request.db
        self.group_service = request.find_service(name='group')

    def __call__(self, _):
        groups = self.group_service.groupids_readable_by(self.user)
        return {'terms': {'group': groups}}
