import pytest
from h_matchers import Any

from h.presenters.organization_json import OrganizationJSONPresenter


class TestOrganizationJSONPresenter:
    def test_it(self, presenter, organization, pyramid_request):
        assert presenter.asdict() == {
            "name": organization.name,
            "id": organization.pubid,
            "default": organization.is_default,
            "logo": pyramid_request.route_url(
                "organization_logo", pubid=organization.pubid
            ),
        }

    def test_summary(self, presenter):
        results = presenter.asdict(summary=True)

        assert results == Any.dict.containing(
            {
                "name": Any(),
                "logo": Any(),
            }
        )

    def test_it_with_no_logo(self, presenter, organization):
        organization.logo = None

        assert presenter.asdict()["logo"] is None

    @pytest.fixture
    def presenter(self, organization, pyramid_request):
        return OrganizationJSONPresenter(organization, pyramid_request)

    @pytest.fixture
    def organization(self, factories):
        return factories.Organization(logo="<svg>Fancy logo</svg>")

    @pytest.fixture(autouse=True)
    def with_logo_route(self, pyramid_config):
        pyramid_config.add_route("organization_logo", "/organizations/{pubid}/logo")
