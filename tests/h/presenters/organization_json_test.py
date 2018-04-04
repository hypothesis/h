# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.presenters.organization_json import OrganizationJSONPresenter
from h.resources import OrganizationResource


class TestOrganizationJSONPresenter(object):
    def test_organization_asdict_no_logo(self, factories, pyramid_request):
        organization = factories.Organization(name='My Org', logo=None)
        organization_resource = OrganizationResource(organization, pyramid_request)

        presenter = OrganizationJSONPresenter(organization_resource)

        assert presenter.asdict() == {
            'name': 'My Org',
            'id': organization.pubid,
            'logo': None,
        }

    def test_organization_asdict_with_logo(self, factories, routes, pyramid_request):
        organization = factories.Organization(name='My Org', logo='<svg>H</svg>')
        organization_resource = OrganizationResource(organization, pyramid_request)

        presenter = OrganizationJSONPresenter(organization_resource)

        assert presenter.asdict() == {
            'name': 'My Org',
            'id': organization_resource.id,
            'logo': pyramid_request.route_url('organization_logo', pubid=organization.pubid)
        }


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('organization_logo', '/organizations/{pubid}/logo')
