# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.presenters.organization_json import OrganizationJSONPresenter


class GroupJSONPresenter(object):
    """Present a group in the JSON format returned by API requests."""

    def __init__(self, group_context):
        self.context = group_context
        self.organization_context = self.context.organization
        self.group = group_context.group

    def asdict(self, expand=[]):
        model = self._model()
        self._expand(model, expand)
        model["links"] = self.context.links or {}
        return model

    def _expand(self, model, expand=[]):
        if "organization" in expand:
            model["organization"] = OrganizationJSONPresenter(
                self.organization_context
            ).asdict()
        return model

    def _model(self):
        model = {
            "id": self.context.id,
            "name": self.group.name,
            "organization": self.organization_context.id,
            "public": self.group.is_public,  # DEPRECATED: TODO: remove from client
            "scoped": True if self.group.scopes else False,
            "type": self.group.type,
        }
        return model


class GroupsJSONPresenter(object):
    """Present a list of groups as JSON"""

    def __init__(self, group_contexts):
        self.contexts = group_contexts

    def asdicts(self, expand=[]):
        return [
            GroupJSONPresenter(group_context).asdict(expand=expand)
            for group_context in self.contexts
        ]
