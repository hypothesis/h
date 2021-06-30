from unittest import mock

import pytest

from h.traversal.organization import (
    OrganizationContext,
    OrganizationLogoRoot,
    OrganizationRoot,
)


@pytest.mark.usefixtures("organizations")
class TestOrganizationRoot:
    def test_it_returns_the_requested_organization(
        self, organizations, organization_factory
    ):
        organization = organizations[1]

        assert organization_factory[organization.pubid] == organization

    def test_it_404s_if_the_organization_doesnt_exist(self, organization_factory):
        with pytest.raises(KeyError):
            organization_factory["does_not_exist"]

    @pytest.fixture
    def organization_factory(self, pyramid_request):
        return OrganizationRoot(pyramid_request)


@pytest.mark.usefixtures("organizations")
class TestOrganizationLogoRoot:
    def test_it_returns_the_requested_organizations_logo(
        self, organizations, organization_logo_factory
    ):
        organization = organizations[1]
        organization.logo = "<svg>blah</svg>"

        assert organization_logo_factory[organization.pubid] == "<svg>blah</svg>"

    def test_it_404s_if_the_organization_doesnt_exist(self, organization_logo_factory):
        with pytest.raises(KeyError):
            organization_logo_factory["does_not_exist"]

    def test_it_404s_if_the_organization_has_no_logo(
        self, organizations, organization_logo_factory
    ):
        with pytest.raises(KeyError):
            assert organization_logo_factory[organizations[0].pubid]

    @pytest.fixture
    def organization_logo_factory(self, pyramid_request):
        return OrganizationLogoRoot(pyramid_request)


class TestOrganizationContext:
    def test_it_returns_organization_model_as_property(
        self, factories, pyramid_request
    ):
        organization = factories.Organization()

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.organization == organization

    def test_it_returns_links_property(self, factories, pyramid_request):
        organization = factories.Organization()

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.links == {}

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


@pytest.fixture
def organizations(factories):
    # Add a handful of organizations to the DB to make the test realistic.
    return [factories.Organization() for _ in range(3)]
