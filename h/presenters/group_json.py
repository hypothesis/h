# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class GroupJSONPresenter(object):
    """Present a group in the JSON format returned by API requests."""

    def __init__(self, group, link_svc=None):
        self.group = group
        self._link_svc = link_svc

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

        if 'group' in model['urls']:
            model['url'] = model['urls']['group']

        return model

    def _inject_urls(self, group, model):
        if not self._link_svc:
            model['urls'] = {}
            return model
        links = self._link_svc(group)
        model['urls'] = links or {}
        return model


class GroupsJSONPresenter(object):
    """Present a list of groups as JSON"""

    def __init__(self, groups, link_svc=None):
        self.groups = groups
        self._link_svc = link_svc

    def asdicts(self):
        return [GroupJSONPresenter(group, self._link_svc).asdict() for group in self.groups]
