from unittest import mock
from unittest.mock import sentinel

import pytest

from h.traversal.organization import OrganizationContext, OrganizationRoot


@pytest.mark.usefixtures("organization_service")
class TestOrganizationRoot:
    def test_it_returns_the_requested_organization(
        self, pyramid_request, organization_service
    ):
        result = OrganizationRoot(pyramid_request)[sentinel.pubid]

        assert result == organization_service.get_by_public_id.return_value
        organization_service.get_by_public_id.assert_called_once_with(sentinel.pubid)

    def test_it_404s_if_the_organization_doesnt_exist(
        self, pyramid_request, organization_service
    ):
        organization_service.get_by_public_id.return_value = None

        with pytest.raises(KeyError):
            OrganizationRoot(pyramid_request)[sentinel.non_existent_pubid]

    @pytest.fixture
    def with_noise_organization(self, factories):
        # Add a handful of organizations to the DB to make the test realistic.
        factories.Organization.generate_batch(size=2)


class TestOrganizationContext:
    def test_it_returns_organization_model_as_property(
        self, factories, pyramid_request
    ):
        organization = factories.Organization()

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.organization == organization

    def test_it_returns_logo_property_as_route_url(self, factories, pyramid_request):
        fake_logo = "<svg>H</svg>"
        pyramid_request.route_url = mock.Mock()

        organization = factories.Organization(logo=fake_logo)

        organization_context = OrganizationContext(organization, pyramid_request)
        logo = organization_context.logo

        pyramid_request.route_url.assert_called_with(
            "organization_logo", pubid=organization.pubid
        )
        assert logo is not None

    def test_it_returns_none_for_logo_if_no_logo(self, factories, pyramid_request):
        pyramid_request.route_url = mock.Mock()

        organization = factories.Organization(logo=None)

        organization_context = OrganizationContext(organization, pyramid_request)
        logo = organization_context.logo

        pyramid_request.route_url.assert_not_called
        assert logo is None

    @pytest.fixture(autouse=True)
    def organization_routes(self, pyramid_config):
        pyramid_config.add_route("organization_logo", "/organization/{pubid}/logo")
