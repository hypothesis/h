# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class GroupJSONPresenter(object):
    """Present a group in the JSON format returned by API requests."""

    def __init__(self, group, route_url=None):
        self.group = group
        self._route_url = route_url

    def asdict(self):
        model = {
          'name': self.group.name,
          'id': self.group.pubid,
          'public': self.group.is_public,
          'scoped': False,  # TODO
          'type': 'open' if self.group.is_public else 'private'  # TODO
        }
        model = self._inject_urls(model)
        return model

    def _inject_urls(self, model):
        model['urls'] = {}
        if not self._route_url:
            return model

        model['url'] = self._route_url('group_read',
                                       pubid=self.group.pubid,
                                       slug=self.group.slug)
        model['urls']['group'] = model['url']
        return model
