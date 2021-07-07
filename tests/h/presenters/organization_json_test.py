import pytest

from h.presenters.organization_json import OrganizationJSONPresenter


class TestOrganizationJSONPresenter:
    def test_it(self, factories, pyramid_request):
        organization = factories.Organization(logo="<svg>Fancy logo</svg>")

        presenter = OrganizationJSONPresenter(organization, pyramid_request)

        assert presenter.asdict() == {
            "name": organization.name,
            "id": organization.pubid,
            "default": organization.is_default,
            "logo": pyramid_request.route_url(
                "organization_logo", pubid=organization.pubid
            ),
        }

    def test_it_with_no_logo(self, factories, pyramid_request):
        organization = factories.Organization(logo=None)

        presenter = OrganizationJSONPresenter(organization, pyramid_request)

        assert presenter.asdict()["logo"] is None

    @pytest.fixture(autouse=True)
    def with_logo_route(self, pyramid_config):
        pyramid_config.add_route("organization_logo", "/organizations/{pubid}/logo")
