# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class GroupJSONPresenter(object):
    """Present a group in the JSON format returned by API requests."""

    def __init__(self, group, links_svc=None):
        self.group = group
        self._links_svc = links_svc

    def asdict(self, expand=[]):
        model = self._model()
        self._inject_urls(model)
        return model

    def _model(self):
        model = {
          'name': self.group.name,
          'id': self.group.pubid,
          'organization': '',  # unexexpanded org; no link available yet, so empty string by default
          'public': self.group.is_public,  # DEPRECATED: TODO: remove from client
          'scoped': True if self.group.scopes else False,
          'type': self.group.type
        }
        return model

    def _inject_urls(self, model):
        model['links'] = {}
        model['urls'] = {}  # DEPRECATED TODO: remove from client
        if not self._links_svc:
            return model

        model['links'] = self._links_svc.get_all(self.group)
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

    def asdicts(self, expand=[]):
        return [GroupJSONPresenter(group, self._links_svc).asdict(expand=expand) for group in self.groups]
