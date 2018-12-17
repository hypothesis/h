# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import pytest
import mock

from h.models import Organization, User
from h.views.admin import groups
from h.views.admin.groups import GroupCreateController, GroupEditController
from h.services.user import UserService
from h.services.group import GroupService
from h.services.group_create import GroupCreateService
from h.services.group_update import GroupUpdateService
from h.services.group_members import GroupMembersService
from h.services.delete_group import DeleteGroupService
from h.services.list_organizations import ListOrganizationsService


class FakeForm(object):
    def set_appstruct(self, appstruct):
        self.appstruct = appstruct

    def render(self):
        return self.appstruct


def test_index_lists_groups_sorted_by_created_desc(
    pyramid_request, routes, factories, authority
):
    group_list = [
        factories.Group(created=datetime.datetime(2017, 8, 2)),
        factories.Group(created=datetime.datetime(2015, 2, 1)),
        factories.Group(),
        factories.Group(created=datetime.datetime(2013, 2, 1)),
    ]

    ctx = groups.groups_index(None, pyramid_request)

    # We can't avoid getting the Public group back, which is created outside of
    # these tests' sphere of influence. Remove it as it is not feasible to
    # assert where it will appear in creation order.
    filtered_groups = list(
        filter(lambda group: group.pubid != "__world__", ctx["results"])
    )

    expected_groups = [group_list[2], group_list[0], group_list[1], group_list[3]]
    assert filtered_groups == expected_groups


def test_index_paginates_results(pyramid_request, routes, paginate):
    groups.groups_index(None, pyramid_request)

    paginate.assert_called_once_with(pyramid_request, mock.ANY, mock.ANY)


@pytest.mark.parametrize(
    "query,expected_groups",
    [
        # All groups should be returned when there is no query.
        (None, ["BioPub", "ChemPub", "Public"]),
        # Only matching groups should be returned if there is a query.
        ("BioPub", ["BioPub"]),
        ("ChemPub", ["ChemPub"]),
        # Filtering should be case-insensitive.
        ("chem", ["ChemPub"]),
    ],
)
def test_index_filters_results(pyramid_request, factories, query, expected_groups):
    factories.Group(name="BioPub")
    factories.Group(name="ChemPub")

    if query:
        pyramid_request.GET["q"] = query
    ctx = groups.groups_index(None, pyramid_request)

    filtered_group_names = sorted([g.name for g in ctx["results"]])
    assert filtered_group_names == expected_groups


@pytest.mark.usefixtures("group_create_svc", "list_orgs_svc", "routes", "user_svc")
class TestGroupCreateController(object):
    def test_get_sets_form(self, pyramid_request):
        ctrl = GroupCreateController(pyramid_request)

        ctx = ctrl.get()

        assert "form" in ctx

    def test_get_lists_all_organizations(
        self,
        pyramid_request,
        factories,
        default_org,
        CreateAdminGroupSchema,
        list_orgs_svc,
    ):
        GroupCreateController(pyramid_request)

        list_orgs_svc.organizations.assert_called_with()
        schema = CreateAdminGroupSchema.return_value
        (_, call_kwargs) = schema.bind.call_args
        assert call_kwargs["organizations"] == {default_org.pubid: default_org}

    def test_post_handles_form_submission(
        self, pyramid_request, handle_form_submission, matchers
    ):
        ctrl = GroupCreateController(pyramid_request)

        ctrl.post()

        handle_form_submission.assert_called_once_with(
            ctrl.request, ctrl.form, matchers.AnyCallable(), ctrl._template_context
        )

    def test_post_redirects_to_list_view_on_success(
        self,
        pyramid_request,
        group_members_svc,
        matchers,
        routes,
        handle_form_submission,
        default_org,
    ):
        def call_on_success(request, form, on_success, on_failure):
            return on_success(
                {
                    "name": "My New Group",
                    "group_type": "restricted",
                    "creator": pyramid_request.user.username,
                    "description": None,
                    "members": [],
                    "organization": default_org.pubid,
                    "origins": [],
                    "enforce_scope": True,
                }
            )

        handle_form_submission.side_effect = call_on_success
        ctrl = GroupCreateController(pyramid_request)

        response = ctrl.post()

        expected_location = pyramid_request.route_url("admin.groups")
        assert response == matchers.Redirect302To(expected_location)

    @pytest.mark.parametrize("type_", ["open", "restricted"])
    def test_post_creates_group_on_success(
        self,
        factories,
        pyramid_request,
        group_create_svc,
        group_members_svc,
        handle_form_submission,
        type_,
        default_org,
    ):
        creator = pyramid_request.user.username
        member_to_add = factories.User()
        origins = ["https://example.com"]

        def call_on_success(request, form, on_success, on_failure):
            return on_success(
                {
                    "organization": default_org.pubid,
                    "creator": creator,
                    "description": "Whatnot",
                    "group_type": type_,
                    "name": "My New Group",
                    "origins": origins,
                    "members": [member_to_add.username],
                    "enforce_scope": True,
                }
            )

        handle_form_submission.side_effect = call_on_success
        ctrl = GroupCreateController(pyramid_request)

        if type_ == "open":
            create_method = group_create_svc.create_open_group
        else:
            create_method = group_create_svc.create_restricted_group

        create_method.return_value = factories.RestrictedGroup(pubid="testgroup")
        ctrl.post()

        expected_userid = User(
            username=creator, authority=pyramid_request.default_authority
        ).userid

        create_method.assert_called_with(
            name="My New Group",
            userid=expected_userid,
            description="Whatnot",
            origins=origins,
            organization=default_org,
            enforce_scope=True,
        )
        group_members_svc.add_members.assert_called_once_with(
            create_method.return_value, [member_to_add.userid]
        )


@pytest.mark.usefixtures(
    "routes",
    "user_svc",
    "group_svc",
    "group_create_svc",
    "group_update_svc",
    "group_members_svc",
    "list_orgs_svc",
)
class TestGroupEditController(object):
    def test_it_binds_schema(
        self, pyramid_request, group, user_svc, default_org, CreateAdminGroupSchema
    ):

        GroupEditController(group, pyramid_request)

        schema = CreateAdminGroupSchema.return_value
        schema.bind.assert_called_with(
            request=pyramid_request,
            group=group,
            user_svc=user_svc,
            organizations={default_org.pubid: default_org},
        )

    def test_read_renders_form(self, pyramid_request, factories, group):
        factories.Annotation(groupid=group.pubid)
        factories.Annotation(groupid=group.pubid)

        ctrl = GroupEditController(group, pyramid_request)

        ctx = ctrl.read()

        assert ctx["form"] == self._expected_form(group)
        assert ctx["pubid"] == group.pubid
        assert ctx["group_name"] == group.name
        assert ctx["member_count"] == len(group.members)
        assert ctx["annotation_count"] == 2

    def test_read_renders_form_if_group_has_no_creator(self, pyramid_request, group):
        group.creator = None
        ctrl = GroupEditController(group, pyramid_request)

        ctx = ctrl.read()

        assert ctx["form"] == self._expected_form(group)

    def test_read_lists_organizations_in_groups_authority(
        self,
        factories,
        pyramid_request,
        group,
        default_org,
        CreateAdminGroupSchema,
        list_orgs_svc,
    ):
        GroupEditController(group, pyramid_request)

        list_orgs_svc.organizations.assert_called_with(group.authority)
        schema = CreateAdminGroupSchema.return_value
        (_, call_kwargs) = schema.bind.call_args
        assert call_kwargs["organizations"] == {default_org.pubid: default_org}

    def test_update_proxies_to_update_svc_on_success(
        self,
        factories,
        pyramid_request,
        user_svc,
        list_orgs_svc,
        handle_form_submission,
        group_update_svc,
        group,
        GroupScope,
    ):

        updated_creator = factories.User()
        user_svc.fetch.return_value = updated_creator
        updated_org = factories.Organization()

        list_orgs_svc.organizations.return_value.append(updated_org)

        def call_on_success(request, form, on_success, on_failure):
            return on_success(
                {
                    "creator": updated_creator.username,
                    "description": "New description",
                    "group_type": "open",
                    "name": "Updated group",
                    "organization": updated_org.pubid,
                    "origins": ["http://somewhereelse.com", "http://www.gladiolus.org"],
                    "members": [],
                    "enforce_scope": False,
                }
            )

        handle_form_submission.side_effect = call_on_success
        ctrl = GroupEditController(group, pyramid_request)

        ctx = ctrl.update()

        group_update_svc.update.assert_called_once_with(
            group,
            organization=updated_org,
            creator=updated_creator,
            description="New description",
            name="Updated group",
            scopes=[
                GroupScope(origin=o)
                for o in ["http://somewhereelse.com", "http://www.gladiolus.org"]
            ],
            enforce_scope=False,
        )
        assert ctx["form"] == self._expected_form(group)

    def test_update_updates_group_members_on_success(
        self,
        factories,
        pyramid_request,
        group_create_svc,
        user_svc,
        group_members_svc,
        handle_form_submission,
        list_orgs_svc,
    ):
        group = factories.RestrictedGroup(
            pubid="testgroup", organization=factories.Organization()
        )
        list_orgs_svc.organizations.return_value = [group.organization]

        member_a = factories.User()
        member_b = factories.User()

        updated_creator = factories.User()
        user_svc.fetch.return_value = updated_creator

        def call_on_success(request, form, on_success, on_failure):
            return on_success(
                {
                    "authority": pyramid_request.default_authority,
                    "creator": updated_creator.username,
                    "description": "a desc",
                    "group_type": "restricted",
                    "name": "a name",
                    "members": [member_a.username, member_b.username],
                    "organization": group.organization.pubid,
                    "origins": ["http://www.example.com"],
                    "enforce_scope": group.enforce_scope,
                }
            )

        handle_form_submission.side_effect = call_on_success
        ctrl = GroupEditController(group, pyramid_request)

        ctrl.update()

        group_members_svc.update_members.assert_any_call(
            group, [member_a.userid, member_b.userid]
        )

    def test_delete_deletes_group(
        self, group, delete_group_svc, pyramid_request, routes
    ):

        ctrl = GroupEditController(group, pyramid_request)

        ctrl.delete()

        delete_group_svc.delete.assert_called_once_with(group)

    @pytest.fixture
    def group(self, factories):
        return factories.OpenGroup(
            pubid="testgroup", organization=factories.Organization()
        )

    def _expected_form(self, group):
        return {
            "creator": group.creator.username if group.creator else "",
            "description": group.description or "",
            "group_type": group.type,
            "name": group.name,
            "members": [m.username for m in group.members],
            "organization": group.organization.pubid,
            "origins": [s.origin for s in group.scopes],
            "enforce_scope": group.enforce_scope,
        }


@pytest.fixture
def authority():
    return "foo.com"


@pytest.fixture
def GroupScope(patch):
    return patch("h.views.admin.groups.GroupScope")


@pytest.fixture
def pyramid_request(pyramid_request, factories, authority):
    pyramid_request.session = mock.Mock(spec_set=["flash", "get_csrf_token"])
    pyramid_request.user = factories.User(authority=authority)
    pyramid_request.create_form.return_value = FakeForm()
    return pyramid_request


@pytest.fixture
def paginate(patch):
    return patch("h.views.admin.groups.paginator.paginate")


@pytest.fixture
def handle_form_submission(patch):
    return patch("h.views.admin.groups.form.handle_form_submission")


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("admin.groups", "/admin/groups")
    pyramid_config.add_route("admin.groups_create", "/admin/groups/new")
    pyramid_config.add_route("group_read", "/groups/{pubid}/{slug}")


@pytest.fixture
def user_svc(pyramid_config):
    svc = mock.create_autospec(UserService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name="user")
    return svc


@pytest.fixture
def group_svc(pyramid_config):
    svc = mock.create_autospec(GroupService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name="group")
    return svc


@pytest.fixture
def group_create_svc(pyramid_config):
    svc = mock.create_autospec(GroupCreateService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name="group_create")
    return svc


@pytest.fixture
def group_update_svc(pyramid_config):
    svc = mock.create_autospec(GroupUpdateService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name="group_update")
    return svc


@pytest.fixture
def group_members_svc(pyramid_config):
    svc = mock.create_autospec(GroupMembersService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name="group_members")
    return svc


@pytest.fixture
def delete_group_svc(pyramid_config, pyramid_request):
    service = mock.Mock(spec_set=DeleteGroupService(request=pyramid_request))
    pyramid_config.register_service(service, name="delete_group")
    return service


@pytest.fixture
def list_orgs_svc(pyramid_config, db_session):
    svc = mock.Mock(spec_set=ListOrganizationsService(db_session))
    svc.organizations.return_value = [Organization.default(db_session)]
    pyramid_config.register_service(svc, name="list_organizations")
    return svc


@pytest.fixture
def CreateAdminGroupSchema(patch):
    schema = mock.Mock(spec_set=["bind"])
    CreateAdminGroupSchema = patch("h.views.admin.groups.CreateAdminGroupSchema")
    CreateAdminGroupSchema.return_value = schema
    return CreateAdminGroupSchema


@pytest.fixture
def default_org(db_session):
    return Organization.default(db_session)
