# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class OrganizationJSONPresenter(object):
    """Present an organization in the JSON format returned by API requests."""

    def __init__(self, organization_resource):
        self.resource = organization_resource
        self.organization = organization_resource.organization

    def asdict(self):
        return self._model()

    def _model(self):
        model = {
          'id': self.resource.id,
          'logo': self.resource.logo,
          'name': self.organization.name,
        }
        return model
