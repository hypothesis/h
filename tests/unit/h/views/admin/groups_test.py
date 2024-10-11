from unittest import mock

import pytest
from h_matchers import Any

from h.traversal.group import GroupContext
from h.views.admin import groups
from h.views.admin.groups import GroupCreateViews, GroupEditViews


class FakeForm:
    appstruct = None

    def set_appstruct(self, appstruct):
        self.appstruct = appstruct

    def render(self):
        return self.appstruct


@pytest.mark.usefixtures("group_service")
class TestIndex:
    def test_it_paginates_results(self, pyramid_request, paginate):
        groups.groups_index(None, pyramid_request)

        paginate.assert_called_once_with(pyramid_request, Any(), Any())

    def test_it_filters_groups_with_name_param(self, pyramid_request, group_service):
        pyramid_request.params["q"] = "fingers"

        groups.groups_index(None, pyramid_request)

        group_service.filter_by_name.assert_called_once_with(name="fingers")

    @pytest.fixture
    def paginate(self, patch):
        return patch("h.views.admin.groups.paginator.paginate")


@pytest.mark.usefixtures(
    "group_create_service",
    "group_members_service",
    "list_organizations_service",
    "routes",
    "user_service",
    "organization_service",
)
class TestGroupCreateView:
    def test_get_sets_form(self, pyramid_request):
        view = GroupCreateViews(pyramid_request)

        response = view.get()

        assert "form" in response

    def test_init_fetches_all_organizations(
        self, pyramid_request, list_organizations_service
    ):
        GroupCreateViews(pyramid_request)

        list_organizations_service.organizations.assert_called_with()

    def test_init_binds_schema_with_organizations(
        self, pyramid_request, organization, AdminGroupSchema
    ):
        GroupCreateViews(pyramid_request)

        schema = AdminGroupSchema.return_value
        (_, call_kwargs) = schema.bind.call_args
        assert call_kwargs["organizations"] == {organization.pubid: organization}

    def test_post_handles_form_submission(
        self, pyramid_request, handle_form_submission
    ):
        view = GroupCreateViews(pyramid_request)

        view.post()

        handle_form_submission.assert_called_once_with(
            view.request,
            view.form,
            Any.function(),
            view._template_context,  # pylint:disable=protected-access
        )

    def test_post_redirects_to_list_view_on_success(
        self, pyramid_request, matchers, handle_form_submission, base_appstruct
    ):
        def call_on_success(  # pylint:disable=unused-argument
            request, form, on_success, on_failure
        ):
            return on_success(base_appstruct)

        handle_form_submission.side_effect = call_on_success
        view = GroupCreateViews(pyramid_request)

        response = view.post()

        expected_location = pyramid_request.route_url("admin.groups")
        assert response == matchers.Redirect302To(expected_location)

    def test_post_creates_open_group_on_success(
        self,
        pyramid_request,
        group_create_service,
        handle_form_submission,
        organization,
        user_service,
        base_appstruct,
    ):
        def call_on_success(  # pylint:disable=unused-argument
            request, form, on_success, on_failure
        ):
            base_appstruct["group_type"] = "open"
            return on_success(base_appstruct)

        handle_form_submission.side_effect = call_on_success
        view = GroupCreateViews(pyramid_request)

        view.post()

        group_create_service.create_open_group.assert_called_with(
            name="My New Group",
            userid=user_service.fetch.return_value.userid,
            description=None,
            scopes=["http://example.com"],
            organization=organization,
            enforce_scope=True,
        )

    def test_post_creates_restricted_group_on_success(
        self,
        pyramid_request,
        group_create_service,
        handle_form_submission,
        organization,
        user_service,
        base_appstruct,
    ):
        def call_on_success(  # pylint:disable=unused-argument
            request, form, on_success, on_failure
        ):
            base_appstruct["group_type"] = "restricted"
            return on_success(base_appstruct)

        handle_form_submission.side_effect = call_on_success
        view = GroupCreateViews(pyramid_request)

        view.post()

        group_create_service.create_restricted_group.assert_called_with(
            name="My New Group",
            userid=user_service.fetch.return_value.userid,
            description=None,
            scopes=["http://example.com"],
            organization=organization,
            enforce_scope=True,
        )

    def test_post_adds_members_on_success(
        self,
        factories,
        pyramid_request,
        group_create_service,
        group_members_service,
        handle_form_submission,
        user_service,
        base_appstruct,
    ):
        user = factories.User()
        user_service.fetch.return_value = user

        def call_on_success(  # pylint:disable=unused-argument
            request, form, on_success, on_failure
        ):
            base_appstruct["members"] = ["someusername"]
            return on_success(base_appstruct)

        handle_form_submission.side_effect = call_on_success
        view = GroupCreateViews(pyramid_request)

        view.post()

        group_members_service.add_members.assert_called_once_with(
            group_create_service.create_restricted_group.return_value, [user.userid]
        )

    def test_post_with_no_organization(
        self,
        base_appstruct,
        handle_form_submission,
        pyramid_request,
        user_service,
        group_create_service,
    ):
        """Test creating a new group with no organization."""
        base_appstruct["organization"] = None

        def call_on_success(  # pylint:disable=unused-argument
            request, form, on_success, on_failure
        ):
            return on_success(base_appstruct)

        handle_form_submission.side_effect = call_on_success
        view = GroupCreateViews(pyramid_request)

        view.post()

        assert user_service.fetch.call_args[0][1] == pyramid_request.default_authority
        assert (
            group_create_service.create_restricted_group.call_args[1]["organization"]
            is None
        )

    @pytest.fixture
    def base_appstruct(self, pyramid_request, organization):
        return {
            "name": "My New Group",
            "group_type": "restricted",
            "creator": pyramid_request.user.username,
            "description": None,
            "members": [],
            "organization": organization.pubid,
            "scopes": ["http://example.com"],
            "enforce_scope": True,
        }


@pytest.mark.usefixtures(
    "routes",
    "user_service",
    "group_service",
    "group_create_service",
    "group_update_service",
    "group_members_service",
    "list_organizations_service",
)
class TestGroupEditViews:
    def test_it_binds_schema(
        self,
        pyramid_request,
        group,
        user_service,
        organization,
        AdminGroupSchema,
    ):
        GroupEditViews(GroupContext(group), pyramid_request)

        schema = AdminGroupSchema.return_value
        schema.bind.assert_called_with(
            request=pyramid_request,
            group=group,
            user_svc=user_service,
            organizations={organization.pubid: organization},
        )

    def test_read_renders_form(self, pyramid_request, factories, group):
        factories.Annotation(groupid=group.pubid)
        factories.Annotation(groupid=group.pubid)

        view = GroupEditViews(GroupContext(group), pyramid_request)

        response = view.read()

        assert response["form"] == self._expected_form(group)
        assert response["pubid"] == group.pubid
        assert response["group_name"] == group.name
        assert response["member_count"] == len(group.members)
        assert response["annotation_count"] == 2

    def test_read_renders_form_if_group_has_no_creator(self, pyramid_request, group):
        group.creator = None
        view = GroupEditViews(GroupContext(group), pyramid_request)

        response = view.read()

        assert response["form"] == self._expected_form(group)

    def test_read_renders_form_if_group_has_no_organization(
        self, pyramid_request, group
    ):
        group.organization = None
        view = GroupEditViews(GroupContext(group), pyramid_request)

        response = view.read()

        assert response["form"]["organization"] is None

    def test_read_lists_organizations_in_groups_authority(
        self,
        pyramid_request,
        group,
        organization,
        AdminGroupSchema,
        list_organizations_service,
    ):
        GroupEditViews(GroupContext(group), pyramid_request)

        list_organizations_service.organizations.assert_called_with(group.authority)
        schema = AdminGroupSchema.return_value
        (_, call_kwargs) = schema.bind.call_args
        assert call_kwargs["organizations"] == {organization.pubid: organization}

    def test_update_proxies_to_update_service_on_success(
        self,
        factories,
        pyramid_request,
        user_service,
        list_organizations_service,
        handle_form_submission,
        group_update_service,
        group,
        GroupScope,
    ):
        fetched_user = factories.User()
        user_service.fetch.return_value = fetched_user
        updated_org = factories.Organization()

        list_organizations_service.organizations.return_value.append(updated_org)

        def call_on_success(  # pylint:disable=unused-argument
            request, form, on_success, on_failure
        ):
            return on_success(
                {
                    "creator": fetched_user.username,
                    "description": "New description",
                    "group_type": "open",
                    "name": "Updated group",
                    "organization": updated_org.pubid,
                    "scopes": ["http://somewhereelse.com", "http://www.gladiolus.org"],
                    "members": [],
                    "enforce_scope": False,
                }
            )

        handle_form_submission.side_effect = call_on_success
        view = GroupEditViews(GroupContext(group), pyramid_request)

        response = view.update()

        group_update_service.update.assert_called_once_with(
            group,
            organization=updated_org,
            creator=fetched_user,
            description="New description",
            name="Updated group",
            scopes=[
                GroupScope(scope=scope)
                for scope in ["http://somewhereelse.com", "http://www.gladiolus.org"]
            ],
            enforce_scope=False,
        )
        assert response["form"] == self._expected_form(group)

    def test_update_when_group_has_no_organization(
        self, pyramid_request, handle_form_submission, group_update_service, group
    ):
        group.organization = None

        def call_on_success(  # pylint:disable=unused-argument
            request, form, on_success, on_failure
        ):
            return on_success(
                {
                    "creator": "creator",
                    "description": "description",
                    "group_type": "open",
                    "name": "name",
                    # If the user selects no organization when updating a group
                    # then on_success() is called with organization=None.
                    "organization": None,
                    "scopes": [],
                    "members": [],
                    "enforce_scope": False,
                }
            )

        handle_form_submission.side_effect = call_on_success
        view = GroupEditViews(GroupContext(group), pyramid_request)

        view.update()

        assert group_update_service.update.call_args[1]["organization"] is None

    def test_update_updates_group_members_on_success(
        self,
        factories,
        pyramid_request,
        user_service,
        group_members_service,
        handle_form_submission,
        list_organizations_service,
    ):
        group = factories.RestrictedGroup(
            pubid="testgroup", organization=factories.Organization()
        )
        list_organizations_service.organizations.return_value = [group.organization]

        fetched_user = factories.User()
        user_service.fetch.return_value = fetched_user

        def call_on_success(  # pylint:disable=unused-argument
            request, form, on_success, on_failure
        ):
            return on_success(
                {
                    "authority": pyramid_request.default_authority,
                    "creator": fetched_user.username,
                    "description": "a desc",
                    "group_type": "restricted",
                    "name": "a name",
                    "members": ["phil", "sue"],
                    "organization": group.organization.pubid,
                    "scopes": ["http://www.example.com"],
                    "enforce_scope": group.enforce_scope,
                }
            )

        handle_form_submission.side_effect = call_on_success
        view = GroupEditViews(GroupContext(group), pyramid_request)

        view.update()

        group_members_service.update_members.assert_any_call(
            group, [fetched_user.userid, fetched_user.userid]
        )

    def test_delete_deletes_group(self, group, group_delete_service, pyramid_request):
        view = GroupEditViews(GroupContext(group), pyramid_request)

        view.delete()

        group_delete_service.delete.assert_called_once_with(group)

    def _expected_form(self, group):
        return {
            "creator": group.creator.username if group.creator else "",
            "description": group.description or "",
            "group_type": group.type,
            "name": group.name,
            "members": [m.username for m in group.members],
            "organization": group.organization.pubid,
            "scopes": [s.scope for s in group.scopes],
            "enforce_scope": group.enforce_scope,
        }

    @pytest.fixture
    def group(self, factories):
        return factories.OpenGroup(
            pubid="testgroup", organization=factories.Organization()
        )

    @pytest.fixture
    def GroupScope(self, patch):
        return patch("h.views.admin.groups.GroupScope")


@pytest.fixture
def authority():
    return "foo.com"


@pytest.fixture
def pyramid_request(pyramid_request, factories, authority):
    pyramid_request.session = mock.Mock(spec_set=["flash", "get_csrf_token"])
    pyramid_request.user = factories.User(authority=authority)
    pyramid_request.create_form.return_value = FakeForm()
    return pyramid_request


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("admin.groups", "/admin/groups")
    pyramid_config.add_route("admin.groups_create", "/admin/groups/new")
    pyramid_config.add_route("group_read", "/groups/{pubid}/{slug}")


@pytest.fixture
def list_organizations_service(list_organizations_service, organization):
    list_organizations_service.organizations.return_value = [organization]

    return list_organizations_service


@pytest.fixture
def organization(factories):
    return factories.Organization()


@pytest.fixture
def handle_form_submission(patch):
    return patch("h.views.admin.groups.form.handle_form_submission")


@pytest.fixture
def AdminGroupSchema(patch):
    schema = mock.Mock(spec_set=["bind"])
    AdminGroupSchema = patch("h.views.admin.groups.AdminGroupSchema")
    AdminGroupSchema.return_value = schema
    return AdminGroupSchema
