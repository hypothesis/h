from unittest.mock import create_autospec, sentinel

import pytest

from h.traversal.organization import OrganizationContext, OrganizationRoot


@pytest.mark.usefixtures("organization_service")
class TestOrganizationRoot:
    def test_it_returns_the_organization_context(
        self, pyramid_request, organization_service
    ):
        result = OrganizationRoot(pyramid_request)[sentinel.pubid]

        assert isinstance(result, OrganizationContext)
        assert result.organization == organization_service.get_by_public_id.return_value
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
        self, organization, pyramid_request
    ):
        result = OrganizationContext(organization, pyramid_request).organization

        assert result == organization

    def test_logo_url(self, organization, pyramid_request):
        organization.logo = "<svg>H</svg>"

        result = OrganizationContext(organization, pyramid_request).logo_url

        pyramid_request.route_url.assert_called_with(
            "organization_logo", pubid=organization.pubid
        )
        assert result == pyramid_request.route_url.return_value

    def test_logo_url_with_no_logo(self, organization, pyramid_request):
        organization.logo = None

        result = OrganizationContext(organization, pyramid_request).logo_url

        pyramid_request.route_url.assert_not_called()
        assert result is None

    @pytest.fixture
    def organization(self, factories):
        return factories.Organization()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.route_url = create_autospec(pyramid_request.route_url)

        return pyramid_request
