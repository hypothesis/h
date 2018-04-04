# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class OrganizationJSONPresenter(object):
    """Present an organization in the JSON format returned by API requests."""

    def __init__(self, organization_resource):
        self.resource = organization_resource
        self.organization = organization_resource.organization

    def asdict(self):
        model = self._model()
        self._logo(model)
        return model

    def _model(self):
        model = {
          'name': self.organization.name,
          'id': self.organization.pubid,
        }
        return model

    def _logo(self, model):
        if self.resource.logo is not None:
            model['logo'] = self.resource.logo
