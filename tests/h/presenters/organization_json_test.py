import pytest

from h.presenters.organization_json import OrganizationJSONPresenter
from h.traversal import OrganizationContext


class TestOrganizationJSONPresenter:
    def test_organization_asdict_no_logo(self, factories, pyramid_request):
        organization = factories.Organization(name="My Org", logo=None)
        organization_context = OrganizationContext(organization, pyramid_request)

        presenter = OrganizationJSONPresenter(organization_context)

        assert presenter.asdict() == {
            "name": "My Org",
            "id": organization.pubid,
            "default": False,
            "logo": None,
        }

    def test_organization_asdict_with_logo(self, factories, routes, pyramid_request):
        organization = factories.Organization(name="My Org", logo="<svg>H</svg>")
        organization_context = OrganizationContext(organization, pyramid_request)

        presenter = OrganizationJSONPresenter(organization_context)

        assert presenter.asdict() == {
            "name": "My Org",
            "id": organization_context.id,
            "default": False,
            "logo": pyramid_request.route_url(
                "organization_logo", pubid=organization.pubid
            ),
        }

    def test_default_organization(
        self, db_session, routes, pyramid_request, default_organization
    ):
        organization_context = OrganizationContext(
            default_organization, pyramid_request
        )

        presenter = OrganizationJSONPresenter(organization_context)
        presented = presenter.asdict()

        assert presented["default"] is True


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("organization_logo", "/organizations/{pubid}/logo")
