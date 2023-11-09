import pytest
from h_matchers import Any

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

    def test_get_by_public_id(self, service, factories):
        organization = factories.Organization()

        result = service.get_by_public_id(organization.pubid)

        assert result == organization

    def test_get_by_public_with_no_match(self, service):
        result = service.get_by_public_id("no_matching_org")

        assert result is None

    def test_get_default(self, service, default_organization):
        assert service.get_default() == default_organization

    @pytest.mark.usefixtures("with_no_default_organization")
    def test_get_default_if_there_is_no_default(self, service):
        assert service.get_default() is None

    @pytest.mark.usefixtures("with_no_default_organization")
    def test_get_default_will_create_with_authority_provided(self, service):
        default_org = service.get_default(authority="my.new.authority")

        assert default_org.name == "Hypothesis"
        assert default_org.authority == "my.new.authority"
        assert default_org.pubid == Organization.DEFAULT_PUBID
        assert default_org.logo == Any.string.containing("<svg")

    @pytest.fixture
    def with_no_default_organization(self, default_organization, db_session):
        # We can't delete the default organization, as it causes foreign key
        # errors but we can alter it so it's not the default any more
        default_organization.pubid = "not_the_default"
        db_session.add(default_organization)
        db_session.flush()

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
