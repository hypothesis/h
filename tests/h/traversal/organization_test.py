from unittest.mock import sentinel

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

    @pytest.fixture(autouse=True)
    def with_noise_organization(self, factories):
        # Add a handful of organizations to the DB to make the test realistic.
        factories.Organization.create_batch(size=2)


class TestOrganizationContext:
    def test_it_returns_parent(self, Root):
        context = OrganizationContext(sentinel.request, sentinel.organization)

        assert context.__parent__ == Root.return_value
        Root.assert_called_once_with(sentinel.request)

    @pytest.fixture
    def Root(self, patch):
        return patch("h.traversal.organization.Root")
