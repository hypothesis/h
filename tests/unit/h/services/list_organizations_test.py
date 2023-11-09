import pytest

from h.services.list_organizations import (
    ListOrganizationsService,
    list_organizations_factory,
)


class TestListOrganizations:
    ALT_AUTHORITY = "bar.com"

    def test_returns_all_organizations_if_no_authority_specified(self, svc):
        results = svc.organizations()

        names = [org.name for org in results]

        # The "Hypothesis" here is from the default org added by DB init
        assert names == ["Hypothesis", "alt_org_1", "alt_org_2", "org_1", "org_2"]

    def test_returns_organizations_for_the_authority_specified(self, svc):
        results = svc.organizations(authority=self.ALT_AUTHORITY)

        names = [org.name for org in results]
        assert names == ["alt_org_1", "alt_org_2"]

    @pytest.fixture(autouse=True)
    def organizations(self, factories, pyramid_request):
        # Add these out of order so it will come back out of order if unsorted
        authority = pyramid_request.default_authority

        return [
            factories.Organization(name="org_2", authority=authority),
            factories.Organization(name="org_1", authority=authority),
        ]

    @pytest.fixture(autouse=True)
    def alt_organizations(self, factories):
        # Add these out of order so it will come back out of order if unsorted
        return [
            factories.Organization(name="alt_org_2", authority=self.ALT_AUTHORITY),
            factories.Organization(name="alt_org_1", authority=self.ALT_AUTHORITY),
        ]

    @pytest.fixture
    def svc(self, db_session):
        return ListOrganizationsService(session=db_session)


class TestListOrganizationsFactory:
    def test_list_organizations_factory(self, pyramid_request):
        svc = list_organizations_factory(None, pyramid_request)

        assert isinstance(svc, ListOrganizationsService)

    def test_provides_request_db_as_session(self, pyramid_request):
        svc = list_organizations_factory(None, pyramid_request)

        assert svc._session == pyramid_request.db  # pylint:disable=protected-access
