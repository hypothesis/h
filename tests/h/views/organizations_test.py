from unittest import mock

import pytest
from pyramid.exceptions import NotFound

from h.views.organizations import organization_logo


class TestOrganizationLogo:
    def test_it_returns_the_logo(self, organization):
        organization.logo = "some logo content"
        result = organization_logo(organization, mock.sentinel.request)

        assert result == organization.logo

    def test_it_raises_a_NotFound_error_for_no_logo(self, organization):
        organization.logo = None

        with pytest.raises(NotFound):
            organization_logo(organization, mock.sentinel.request)

    @pytest.fixture
    def organization(self, factories):
        return factories.Organization()
