# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class GroupJSONPresenter(object):
    """Present a group in the JSON format returned by API requests."""

    def __init__(self, group, route_url=None):
        self.group = group
        self._route_url = route_url

    def asdict(self):
        return self._model(self.group)

    def _model(self, group):
        model = {
          'name': group.name,
          'id': group.pubid,
          'public': group.is_public,
          'scoped': False,  # TODO
          'type': 'open' if group.is_public else 'private'  # TODO
        }
        model = self._inject_urls(group, model)
        return model

    def _inject_urls(self, group, model):
        model['urls'] = {}
        if not self._route_url:
            return model

        model['url'] = self._route_url('group_read',
                                       pubid=group.pubid,
                                       slug=group.slug)
        model['urls']['group'] = model['url']
        return model


class GroupsJSONPresenter(GroupJSONPresenter):
    """Present a list of groups as JSON"""

    def __init__(self, groups, route_url=None):
        self.groups = groups
        self._route_url = route_url

    def asdicts(self):
        return [self._model(group) for group in self.groups]
