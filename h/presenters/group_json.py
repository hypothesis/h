# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.presenters.organization_json import OrganizationJSONPresenter


class GroupJSONPresenter(object):
    """Present a group in the JSON format returned by API requests."""

    def __init__(self, group_resource):
        self.resource = group_resource
        self.organization_resource = self.resource.organization
        self.group = group_resource.group

    def asdict(self, expand=[]):
        model = self._model()
        self._expand(model, expand)
        self._inject_urls(model)
        return model

    def _expand(self, model, expand=[]):
        if 'organization' in expand:
            model['organization'] = OrganizationJSONPresenter(
              self.organization_resource
            ).asdict()
        return model

    def _model(self):
        model = {
          'id': self.resource.id,
          'name': self.group.name,
          'organization': self.organization_resource.id,
          'public': self.group.is_public,  # DEPRECATED: TODO: remove from client
          'scoped': True if self.group.scopes else False,
          'type': self.group.type
        }
        return model

    def _inject_urls(self, model):
        model['links'] = self.resource.links or {}
        model['urls'] = model['links']  # DEPRECATED TODO: remove from client
        if 'html' in model['links']:
            # DEPRECATED TODO: remove from client
            model['url'] = model['urls']['html']
        return model


class GroupsJSONPresenter(object):
    """Present a list of groups as JSON"""

    def __init__(self, group_resources):
        self.resources = group_resources

    def asdicts(self, expand=[]):
        return [GroupJSONPresenter(group_resource).asdict(expand=expand) for group_resource in self.resources]
