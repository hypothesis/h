# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class GroupJSONPresenter(object):
    """Present a group in the JSON format returned by API requests."""

    def __init__(self, group, links_svc=None):
        self.group = group
        self._links_svc = links_svc

    def asdict(self):
        return self._model(self.group)

    def _model(self, group):
        model = {
          'name': group.name,
          'id': group.pubid,
          'public': group.is_public,  # DEPRECATED: TODO: remove from client
          'scoped': True if group.scopes else False,
          'type': group.type
        }
        model = self._inject_urls(group, model)
        return model

    def _inject_urls(self, group, model):
        model['links'] = {}
        model['urls'] = {}  # DEPRECATED TODO: remove from client
        if not self._links_svc:
            return model

        model['links'] = self._links_svc.get_all(group)
        model['urls'] = model['links']  # DEPRECATED TODO: remove from client
        if 'html' in model['links']:
            # DEPRECATED TODO: remove from client
            model['url'] = model['urls']['html']
        return model


class GroupsJSONPresenter(object):
    """Present a list of groups as JSON"""

    def __init__(self, groups, links_svc=None):
        self.groups = groups
        self._links_svc = links_svc

    def asdicts(self):
        return [GroupJSONPresenter(group, self._links_svc).asdict() for group in self.groups]
