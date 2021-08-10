from unittest.mock import Mock

import pytest
from h_matchers import Any

from h.models import Organization
from h.traversal import OrganizationContext
from h.views.admin.organizations import (
    OrganizationCreateController,
    OrganizationEditController,
    index,
)


class FakeForm:
    appstruct = None

    def set_appstruct(self, appstruct):
        self.appstruct = appstruct

    def render(self):
        return self.appstruct


class TestIndex:
    @pytest.mark.parametrize(
        "query,expected_orgs",
        [
            # With no query, all orgs are returned, including the default
            # "Hypothesis" organization.
            (None, ["BioPub", "ChemPub", "Hypothesis"]),
            # With a query, only matching orgs are returned.
            ("bio", ["BioPub"]),
        ],
    )
    @pytest.mark.usefixtures("orgs")
    def test_it_returns_filtered_orgs(self, pyramid_request, query, expected_orgs):
        if query:
            pyramid_request.GET["q"] = query

        response = index(None, pyramid_request)

        filtered_orgs = sorted([org.name for org in response["results"]])
        assert filtered_orgs == expected_orgs

    @pytest.fixture
    def orgs(self, factories):
        return [
            factories.Organization(name="BioPub"),
            factories.Organization(name="ChemPub"),
        ]


@pytest.mark.usefixtures("routes")
class TestOrganizationCreateController:
    @staticmethod
    def call_on_success(  # pylint: disable=unused-argument
        request, form, on_success, on_failure
    ):
        return on_success(
            {
                "name": "New organization",
                "authority": "example.organization",
                "logo": "<svg>a logo</svg>",
            }
        )

    def test_get_sets_default_values(self, pyramid_request):
        controller = OrganizationCreateController(pyramid_request)

        response = controller.get()

        assert response["form"] == {"authority": pyramid_request.default_authority}

    def test_post_creates_org(self, pyramid_request, handle_form_submission):
        handle_form_submission.side_effect = self.call_on_success
        controller = OrganizationCreateController(pyramid_request)

        controller.post()

        org = (
            pyramid_request.db.query(Organization)
            .filter_by(name="New organization")
            .one()
        )
        assert org.authority == "example.organization"
        assert org.logo == "<svg>a logo</svg>"

    def test_post_redirects_to_list_view(
        self, pyramid_request, handle_form_submission, matchers
    ):
        handle_form_submission.side_effect = self.call_on_success
        controller = OrganizationCreateController(pyramid_request)

        response = controller.post()

        list_url = pyramid_request.route_url("admin.organizations")
        assert response == matchers.Redirect302To(list_url)


@pytest.mark.usefixtures("routes")
class TestOrganizationEditController:
    def test_read(self, get_controller, pyramid_request, organization):
        response = get_controller().read()

        expected_delete_url = pyramid_request.route_url(
            "admin.organizations_delete", pubid=organization.pubid
        )
        assert response == {
            "form": self._expected_form(organization),
            "delete_url": expected_delete_url,
        }

    def test_logo_is_empty_if_not_set(self, get_controller, organization):
        organization.logo = None

        response = get_controller().read()

        assert not response["form"]["logo"]

    def test_read_does_not_show_delete_button_for_default_org(
        self, get_controller, organization
    ):
        organization.pubid = Organization.DEFAULT_PUBID

        response = get_controller().read()

        assert response["delete_url"] is None

    def test_update_saves_org(
        self, get_controller, organization, handle_form_submission
    ):
        def call_on_success(  # pylint:disable=unused-argument
            request, form, on_success, on_failure
        ):
            return on_success(
                {
                    "name": "Updated name",
                    "authority": organization.authority,
                    "logo": "<svg>new logo</svg>",
                }
            )

        handle_form_submission.side_effect = call_on_success

        response = get_controller().update()

        assert organization.name == "Updated name"
        assert organization.logo == "<svg>new logo</svg>"
        assert response["form"] == self._expected_form(organization)

    def test_delete(self, get_controller, organization, pyramid_request, matchers):
        response = get_controller().delete()

        assert organization in pyramid_request.db.deleted
        list_url = pyramid_request.route_path("admin.organizations")
        assert response == matchers.Redirect302To(list_url)

    def test_delete_fails_if_org_has_groups(
        self, get_controller, organization, pyramid_request, factories
    ):
        factories.Group(name="Test", organization=organization)

        response = get_controller().delete()

        assert organization not in pyramid_request.db.deleted
        assert pyramid_request.response.status_int == 400
        pyramid_request.session.flash.assert_called_with(
            Any.string.matching(".*Cannot delete.*1 groups"), "error"
        )
        assert response["form"] == self._expected_form(organization)

    def _expected_form(self, organization):
        return {
            "authority": organization.authority,
            "logo": organization.logo,
            "name": organization.name,
        }

    @pytest.fixture
    def get_controller(self, organization, pyramid_request):
        def get_controller():
            return OrganizationEditController(
                OrganizationContext(organization), pyramid_request
            )

        return get_controller

    @pytest.fixture
    def organization(self, factories):
        return factories.Organization(logo="<svg></svg>")


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.session = Mock(spec_set=["flash", "get_csrf_token"])
    pyramid_request.create_form.return_value = FakeForm()
    return pyramid_request


@pytest.fixture
def handle_form_submission(patch):
    return patch("h.views.admin.groups.form.handle_form_submission")


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("admin.organizations", "/admin/organizations")
    pyramid_config.add_route(
        "admin.organizations_delete", "/admin/organizations/delete/{pubid}"
    )
