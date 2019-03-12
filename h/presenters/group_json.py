# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.presenters.organization_json import OrganizationJSONPresenter


class GroupJSONPresenter(object):
    """Present a group in the JSON format returned by API requests."""

    def __init__(self, group_context):
        self.context = group_context
        self.organization_context = self.context.organization
        self.group = group_context.group

    def asdict(self, expand=None):
        if expand is None:
            expand = []

        model = self._model()
        self._expand(model, expand)
        model["links"] = self.context.links or {}
        return model

    def _expand(self, model, expand):
        if "organization" in expand:
            if self.organization_context:
                model["organization"] = OrganizationJSONPresenter(
                    self.organization_context
                ).asdict()
        if "scopes" in expand:
            model["scopes"] = {}
            # The API representation of scope enforcement differs from the DB
            # representation. All groups have an `enforce_scope` property, and
            # it defaults to True. However, URL enforcement for incoming
            # annotations only happens if there are 1 or more scopes to restrict
            # to. Therefore, the API representation of this property is False
            # if there are no scopes.
            model["scopes"]["enforced"] = (
                self.group.enforce_scope if self.group.scopes else False
            )
            # At this presentation layer, format scopes to look like
            # patterns—currently a simple wildcarded prefix—to give us more
            # flexibility in making scope more granular later
            model["scopes"]["uri_patterns"] = [
                scope.scope + "*" for scope in self.group.scopes
            ]
        return model

    def _model(self):
        organization = None
        if self.organization_context:
            organization = self.organization_context.id
        model = {
            "id": self.context.id,
            "groupid": self.group.groupid,
            "name": self.group.name,
            "organization": organization,
            "public": self.group.is_public,  # DEPRECATED: TODO: remove from client
            "scoped": True if self.group.scopes else False,
            "type": self.group.type,
        }
        return model


class GroupsJSONPresenter(object):
    """Present a list of groups as JSON"""

    def __init__(self, group_contexts):
        self.contexts = group_contexts

    def asdicts(self, expand=None):
        return [
            GroupJSONPresenter(group_context).asdict(expand=expand)
            for group_context in self.contexts
        ]
