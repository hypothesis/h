# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class OrganizationJSONPresenter(object):
    """Present an organization in the JSON format returned by API requests."""

    def __init__(self, organization_context):
        self.context = organization_context
        self.organization = organization_context.organization

    def asdict(self):
        return self._model()

    def _model(self):
        model = {
            "id": self.context.id,
            "default": self.context.default,
            "logo": self.context.logo,
            "name": self.organization.name,
        }
        return model
