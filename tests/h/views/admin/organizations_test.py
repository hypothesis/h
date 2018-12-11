from __future__ import unicode_literals

from mock import Mock
import pytest

from h.models import Organization
from h.views.admin.organizations import (
    index,
    OrganizationCreateController,
    OrganizationEditController,
)


class FakeForm(object):
    def set_appstruct(self, appstruct):
        self.appstruct = appstruct

    def render(self):
        return self.appstruct


class TestIndex(object):
    @pytest.mark.parametrize(
        "query,expected_orgs",
        [
            # With no query, all orgs are returned, including the default
            # "Hypothesis" org.
            (None, ["BioPub", "ChemPub", "Hypothesis"]),
            # With a query, only matching orgs are returned.
            ("bio", ["BioPub"]),
        ],
    )
    def test_it_returns_filtered_orgs(
        self, orgs, pyramid_request, query, expected_orgs
    ):
        if query:
            pyramid_request.GET["q"] = query

        ctx = index(None, pyramid_request)

        filtered_orgs = sorted([org.name for org in ctx["results"]])
        assert filtered_orgs == expected_orgs

    @pytest.fixture
    def orgs(self, factories):
        return [
            factories.Organization(name="BioPub"),
            factories.Organization(name="ChemPub"),
        ]


@pytest.mark.usefixtures("routes")
class TestOrganizationCreateController(object):
    def test_get_sets_default_values(self, pyramid_request):
        ctrl = OrganizationCreateController(pyramid_request)

        ctx = ctrl.get()

        assert ctx["form"] == {"authority": pyramid_request.default_authority}

    def test_post_creates_org(self, pyramid_request, handle_form_submission):
        def call_on_success(request, form, on_success, on_failure):
            return on_success(
                {
                    "name": "New org",
                    "authority": "example.org",
                    "logo": "<svg>a logo</svg>",
                }
            )

        handle_form_submission.side_effect = call_on_success
        ctrl = OrganizationCreateController(pyramid_request)

        ctrl.post()

        org = pyramid_request.db.query(Organization).filter_by(name="New org").one()
        assert org.authority == "example.org"
        assert org.logo == "<svg>a logo</svg>"

    def test_post_redirects_to_list_view(
        self, pyramid_request, handle_form_submission, matchers
    ):
        def call_on_success(request, form, on_success, on_failure):
            return on_success(
                {
                    "name": "New org",
                    "authority": "example.org",
                    "logo": "<svg>a logo</svg>",
                }
            )

        handle_form_submission.side_effect = call_on_success
        ctrl = OrganizationCreateController(pyramid_request)

        response = ctrl.post()

        list_url = pyramid_request.route_url("admin.organizations")
        assert response == matchers.Redirect302To(list_url)


@pytest.mark.usefixtures("routes")
class TestOrganizationEditController(object):
    def test_read_presents_org(self, pyramid_request, org):
        ctrl = OrganizationEditController(org, pyramid_request)
        ctx = ctrl.read()
        assert ctx["form"] == self._expected_form(org)

    def test_logo_is_empty_if_not_set(self, pyramid_request, org):
        org.logo = None
        ctrl = OrganizationEditController(org, pyramid_request)

        ctx = ctrl.read()

        assert ctx["form"]["logo"] == ""

    def test_read_shows_delete_button(self, pyramid_request, org):
        ctrl = OrganizationEditController(org, pyramid_request)
        ctx = ctrl.read()
        assert ctx["delete_url"] == pyramid_request.route_url(
            "admin.organizations_delete", pubid=org.pubid
        )

    def test_read_does_not_show_delete_button_for_default_org(
        self, pyramid_request, org
    ):
        org.pubid = "__default__"
        ctrl = OrganizationEditController(org, pyramid_request)

        ctx = ctrl.read()

        assert ctx["delete_url"] is None

    def test_update_saves_org(self, pyramid_request, org, handle_form_submission):
        def call_on_success(request, form, on_success, on_failure):
            return on_success(
                {
                    "name": "Updated name",
                    "authority": org.authority,
                    "logo": "<svg>new logo</svg>",
                }
            )

        handle_form_submission.side_effect = call_on_success
        ctrl = OrganizationEditController(org, pyramid_request)

        ctx = ctrl.update()

        assert org.name == "Updated name"
        assert org.logo == "<svg>new logo</svg>"
        assert ctx["form"] == self._expected_form(org)

    def test_delete_removes_org(self, pyramid_request, db_session, org):
        ctrl = OrganizationEditController(org, pyramid_request)
        ctrl.delete()
        assert org in db_session.deleted

    def test_delete_redirects_to_org_list(self, matchers, org, pyramid_request):
        ctrl = OrganizationEditController(org, pyramid_request)

        response = ctrl.delete()

        list_url = pyramid_request.route_path("admin.organizations")
        assert response == matchers.Redirect302To(list_url)

    def test_delete_fails_if_org_has_groups(
        self, factories, matchers, org, pyramid_request
    ):
        factories.Group(name="Test", organization=org)
        ctrl = OrganizationEditController(org, pyramid_request)

        ctx = ctrl.delete()

        assert org not in pyramid_request.db.deleted
        assert pyramid_request.response.status_int == 400
        pyramid_request.session.flash.assert_called_with(
            matchers.Regex(".*Cannot delete.*1 groups"), "error"
        )
        assert ctx["form"] == self._expected_form(org)

    def _expected_form(self, org):
        return {"authority": org.authority, "logo": org.logo, "name": org.name}

    @pytest.fixture
    def org(self, factories):
        return factories.Organization(name="FooPub", logo="<svg></svg>")


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
