# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.presenters.organization_json import OrganizationJSONPresenter


class GroupJSONPresenter(object):
    """Present a group in the JSON format returned by API requests."""

    def __init__(self, group_resource):
        self.resource = group_resource
        self.group = group_resource.group

    def asdict(self, expand=[]):
        model = self._model()
        self._expand(model, expand)
        self._inject_urls(model)
        return model

    def _expand(self, model, expand=[]):
        if 'organization' in expand:
            org_resource = self.resource.organization
            if org_resource is not None:
                model['organization'] = OrganizationJSONPresenter(org_resource).asdict()
            else:
                model['organization'] = {}
        return model

    def _model(self):
        model = {
          'name': self.group.name,
          'id': self.group.pubid,
          'organization': '',  # unexpanded org; no link available yet, so empty string by default
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
