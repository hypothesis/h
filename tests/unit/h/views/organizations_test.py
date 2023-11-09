from unittest import mock

import pytest
from pyramid.exceptions import NotFound

from h.traversal import OrganizationContext
from h.views.organizations import organization_logo


class TestOrganizationLogo:
    def test_it_returns_the_logo(self, organization_context):
        organization_context.organization.logo = "some logo content"
        result = organization_logo(organization_context, mock.sentinel.request)

        assert result == organization_context.organization.logo

    def test_it_raises_a_NotFound_error_for_no_logo(self, organization_context):
        organization_context.organization.logo = None

        with pytest.raises(NotFound):
            organization_logo(organization_context, mock.sentinel.request)

    @pytest.fixture
    def organization_context(self, factories):
        return OrganizationContext(factories.Organization())
