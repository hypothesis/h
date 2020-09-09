import pytest

from h.models import Organization
from h.services.organization import OrganizationService, organization_factory


class TestOrganizationService:
    def test_create_returns_organization(self, service):
        organization = service.create(
            name="Organization", authority="publisher.com", logo="<svg>H</svg>"
        )

        assert isinstance(organization, Organization)

    def test_create_with_default_logo_returns_organization(self, service):
        organization = service.create(name="Organization", authority="publisher.com")

        assert isinstance(organization, Organization)
        assert organization.logo is None

    @pytest.fixture
    def service(self, db_session):
        return OrganizationService(db_session)


class TestOrganizationsFactory:
    def test_returns_organizations_service(self, pyramid_request):
        svc = organization_factory(None, pyramid_request)

        assert isinstance(svc, OrganizationService)

    def test_provides_request_db_as_session(self, pyramid_request):
        svc = organization_factory(None, pyramid_request)

        assert svc.session == pyramid_request.db
