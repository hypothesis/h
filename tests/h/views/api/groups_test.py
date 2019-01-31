# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import (
    HTTPNoContent,
    HTTPBadRequest,
    HTTPNotFound,
    HTTPConflict,
)

from h.views.api import groups as views
from h.services.group_list import GroupListService
from h.services.group import GroupService
from h.services.group_create import GroupCreateService
from h.services.group_update import GroupUpdateService
from h.services.group_members import GroupMembersService
from h.services.user import UserService
from h.services.group_links import GroupLinksService
from h import traversal

pytestmark = pytest.mark.usefixtures("GroupsJSONPresenter")


@pytest.mark.usefixtures("group_list_service", "group_links_service")
class TestGetGroups(object):
    def test_proxies_to_list_service(self, anonymous_request, group_list_service):
        views.groups(anonymous_request)

        group_list_service.request_groups.assert_called_once_with(
            user=None, authority=None, document_uri=None
        )

    def test_proxies_request_params(self, anonymous_request, group_list_service):
        anonymous_request.params["document_uri"] = "http://example.com/thisthing.html"
        anonymous_request.params["authority"] = "foo.com"
        views.groups(anonymous_request)

        group_list_service.request_groups.assert_called_once_with(
            user=None,
            authority="foo.com",
            document_uri="http://example.com/thisthing.html",
        )

    def test_converts_groups_to_resources(
        self, GroupContext, anonymous_request, open_groups, group_list_service
    ):
        group_list_service.request_groups.return_value = open_groups

        views.groups(anonymous_request)

        GroupContext.assert_has_calls(
            [
                mock.call(open_groups[0], anonymous_request),
                mock.call(open_groups[1], anonymous_request),
            ]
        )

    def test_uses_presenter_for_formatting(
        self,
        group_links_service,
        open_groups,
        group_list_service,
        GroupsJSONPresenter,
        anonymous_request,
    ):
        group_list_service.request_groups.return_value = open_groups

        views.groups(anonymous_request)

        GroupsJSONPresenter.assert_called_once()

    def test_returns_dicts_from_presenter(
        self, anonymous_request, open_groups, group_list_service, GroupsJSONPresenter
    ):
        group_list_service.request_groups.return_value = open_groups

        result = views.groups(anonymous_request)

        assert result == GroupsJSONPresenter(open_groups).asdicts.return_value

    def test_proxies_expand_to_presenter(
        self, anonymous_request, open_groups, group_list_service, GroupsJSONPresenter
    ):
        anonymous_request.params["expand"] = "organization"
        group_list_service.request_groups.return_value = open_groups

        views.groups(anonymous_request)

        GroupsJSONPresenter(open_groups).asdicts.assert_called_once_with(
            expand=["organization"]
        )

    def test_passes_multiple_expand_to_presenter(
        self, anonymous_request, open_groups, group_list_service, GroupsJSONPresenter
    ):
        anonymous_request.GET.add("expand", "organization")
        anonymous_request.GET.add("expand", "foobars")
        group_list_service.request_groups.return_value = open_groups

        views.groups(anonymous_request)

        GroupsJSONPresenter(open_groups).asdicts.assert_called_once_with(
            expand=["organization", "foobars"]
        )

    @pytest.fixture
    def open_groups(self, factories):
        return [factories.OpenGroup(), factories.OpenGroup()]

    @pytest.fixture
    def authenticated_request(self, pyramid_request, factories):
        pyramid_request.user = factories.User()
        return pyramid_request


@pytest.mark.usefixtures(
    "CreateGroupAPISchema",
    "group_service",
    "group_create_service",
    "GroupContext",
    "GroupJSONPresenter",
)
class TestCreateGroup(object):
    def test_it_inits_group_create_schema(self, pyramid_request, CreateGroupAPISchema):
        views.create(pyramid_request)

        CreateGroupAPISchema.return_value.validate.assert_called_once_with({})

    # @TODO Move this test once _json_payload() has been moved to a reusable util module
    def test_it_raises_if_json_parsing_fails(self, pyramid_request):
        """It raises PayloadError if parsing of the request body fails."""
        # Make accessing the request.json_body property raise ValueError.
        type(pyramid_request).json_body = {}
        with mock.patch.object(
            type(pyramid_request), "json_body", new_callable=mock.PropertyMock
        ) as json_body:
            json_body.side_effect = ValueError()
            with pytest.raises(views.PayloadError):
                views.create(pyramid_request)

    def test_it_passes_request_params_to_group_create_service(
        self, pyramid_request, CreateGroupAPISchema, group_create_service
    ):
        CreateGroupAPISchema.return_value.validate.return_value = {
            "name": "My Group",
            "description": "How about that?",
        }
        views.create(pyramid_request)

        group_create_service.create_private_group.assert_called_once_with(
            "My Group",
            pyramid_request.user.userid,
            description="How about that?",
            groupid=None,
        )

    def test_it_passes_groupid_to_group_create_as_authority_provided_id(
        self, pyramid_request, CreateGroupAPISchema, group_create_service
    ):
        # Note that CreateGroupAPISchema and its methods are mocked here, so
        # ``groupid`` passes validation even though the request is not third party
        # Tests for that are handled directly in the CreateGroupAPISchema unit tests
        # and through functional tests
        CreateGroupAPISchema.return_value.validate.return_value = {
            "name": "My Group",
            "description": "How about that?",
            "groupid": "group:something@example.com",
        }
        views.create(pyramid_request)

        group_create_service.create_private_group.assert_called_once_with(
            "My Group",
            pyramid_request.user.userid,
            description="How about that?",
            groupid="group:something@example.com",
        )

    def test_it_sets_description_to_none_if_not_present(
        self, pyramid_request, CreateGroupAPISchema, group_create_service
    ):
        CreateGroupAPISchema.return_value.validate.return_value = {"name": "My Group"}
        views.create(pyramid_request)

        group_create_service.create_private_group.assert_called_once_with(
            "My Group", pyramid_request.user.userid, description=None, groupid=None
        )

    def test_it_raises_HTTPConflict_on_duplicate(
        self, pyramid_request, CreateGroupAPISchema, group_service, factories
    ):

        group = factories.Group(
            authority_provided_id="something", authority="example.com"
        )
        group_service.fetch.return_value = group

        with pytest.raises(HTTPConflict, match="group with groupid.*already exists"):
            views.create(pyramid_request)

    def test_it_creates_group_context_from_created_group(
        self, pyramid_request, GroupContext, group_create_service
    ):
        my_group = mock.Mock()
        group_create_service.create_private_group.return_value = my_group

        views.create(pyramid_request)

        GroupContext.assert_called_with(my_group, pyramid_request)

    def test_it_returns_new_group_formatted_with_presenter(
        self, pyramid_request, GroupContext, GroupJSONPresenter
    ):
        views.create(pyramid_request)

        GroupJSONPresenter.assert_called_once_with(GroupContext.return_value)
        GroupJSONPresenter.return_value.asdict.assert_called_once_with(
            expand=["organization", "scopes"]
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request, factories):
        # Add a nominal json_body so that _json_payload() parsing of
        # it doesn't raise
        pyramid_request.json_body = {}
        pyramid_request.user = factories.User()
        return pyramid_request


@pytest.mark.usefixtures("GroupJSONPresenter", "GroupContext")
class TestReadGroup(object):
    def test_it_creates_group_context_from_group_model(
        self, GroupContext, factories, pyramid_request
    ):
        group = factories.Group()

        views.read(group, pyramid_request)

        GroupContext.assert_called_once_with(group, pyramid_request)

    def test_it_forwards_expand_param_to_presenter(
        self, GroupJSONPresenter, factories, pyramid_request
    ):
        pyramid_request.params["expand"] = "organization"
        group = factories.Group()

        views.read(group, pyramid_request)

        GroupJSONPresenter.return_value.asdict.assert_called_once_with(["organization"])

    def test_it_returns_presented_group(
        self, GroupJSONPresenter, factories, pyramid_request
    ):
        pyramid_request.params["expand"] = "organization"
        group = factories.Group()

        presented = views.read(group, pyramid_request)

        assert presented == GroupJSONPresenter.return_value.asdict.return_value


@pytest.mark.usefixtures(
    "UpdateGroupAPISchema",
    "group_service",
    "group_update_service",
    "GroupContext",
    "GroupJSONPresenter",
)
class TestUpdateGroup(object):
    def test_it_inits_group_update_schema(
        self, pyramid_request, group, UpdateGroupAPISchema
    ):
        views.update(group, pyramid_request)

        UpdateGroupAPISchema.return_value.validate.assert_called_once_with({})

    def test_it_passes_request_params_to_group_update_service(
        self, group, pyramid_request, UpdateGroupAPISchema, group_update_service
    ):
        patch_payload = {"name": "My Group", "description": "How about that?"}
        UpdateGroupAPISchema.return_value.validate.return_value = patch_payload
        views.update(group, pyramid_request)

        group_update_service.update.assert_called_once_with(group, **patch_payload)

    def test_it_raises_HTTPConflict_on_duplicate(
        self, pyramid_request, UpdateGroupAPISchema, group_service, factories
    ):

        pre_existing_group = factories.Group(
            authority_provided_id="something", authority="example.com"
        )
        group = factories.Group(
            authority_provided_id="something_else", authority="example.com"
        )
        group_service.fetch.return_value = pre_existing_group

        with pytest.raises(HTTPConflict, match="group with groupid.*already exists"):
            views.update(group, pyramid_request)

    def test_it_does_not_raise_HTTPConflict_if_duplicate_is_same_group(
        self, pyramid_request, UpdateGroupAPISchema, group_service, factories
    ):
        group = factories.Group(
            authority_provided_id="something_else", authority="example.com"
        )
        group_service.fetch.return_value = group

        views.update(group, pyramid_request)

    def test_it_creates_group_context_from_updated_group(
        self, pyramid_request, GroupContext, group_update_service
    ):
        my_group = mock.Mock()
        group_update_service.update.return_value = my_group

        views.update(my_group, pyramid_request)

        GroupContext.assert_called_with(my_group, pyramid_request)

    def test_it_returns_updated_group_formatted_with_presenter(
        self, pyramid_request, GroupContext, GroupJSONPresenter, group
    ):
        views.update(group, pyramid_request)

        GroupJSONPresenter.assert_called_once_with(GroupContext.return_value)
        GroupJSONPresenter.return_value.asdict.assert_called_once_with(
            expand=["organization", "scopes"]
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request, factories):
        # Add a nominal json_body so that _json_payload() parsing of
        # it doesn't raise
        pyramid_request.json_body = {}
        pyramid_request.user = factories.User()
        return pyramid_request

    @pytest.fixture
    def group(self, factories):
        return factories.Group(authority="example.com")


@pytest.mark.usefixtures(
    "create",
    "CreateGroupAPISchema",
    "group_service",
    "group_update_service",
    "GroupContext",
    "GroupJSONPresenter",
)
class TestUpsertGroup(object):
    def test_it_proxies_to_create_if_group_empty(
        self, pyramid_request, create, GroupUpsertContext
    ):
        context = GroupUpsertContext(None, pyramid_request)

        res = views.upsert(context, pyramid_request)

        create.assert_called_once_with(pyramid_request)
        assert res == create.return_value

    def test_it_does_not_proxy_to_create_if_group_extant(
        self, pyramid_request, create, group, GroupUpsertContext
    ):
        context = GroupUpsertContext(group, pyramid_request)

        views.upsert(context, pyramid_request)

        assert create.call_count == 0

    def test_it_validates_against_group_update_schema_if_group_extant(
        self, pyramid_request, group, GroupUpsertContext, CreateGroupAPISchema
    ):
        context = GroupUpsertContext(group, pyramid_request)
        pyramid_request.json_body = {"name": "Rename Group"}

        views.upsert(context, pyramid_request)

        CreateGroupAPISchema.return_value.validate.assert_called_once_with(
            {"name": "Rename Group"}
        )

    def test_it_raises_HTTPConflict_on_duplicate(
        self, pyramid_request, group_service, factories, GroupUpsertContext
    ):

        pre_existing_group = factories.Group(
            authority_provided_id="something", authority="example.com"
        )
        group = factories.Group(
            authority_provided_id="something_else", authority="example.com"
        )

        context = GroupUpsertContext(group, pyramid_request)

        group_service.fetch.return_value = pre_existing_group

        with pytest.raises(HTTPConflict, match="group with groupid.*already exists"):
            views.upsert(context, pyramid_request)

    def test_it_does_not_raise_HTTPConflict_if_duplicate_is_same_group(
        self, pyramid_request, group_service, factories, GroupUpsertContext
    ):
        group = factories.Group(
            authority_provided_id="something_else", authority="example.com"
        )
        context = GroupUpsertContext(group, pyramid_request)
        group_service.fetch.return_value = group

        views.upsert(context, pyramid_request)

    def test_it_proxies_to_update_service_with_injected_defaults(
        self,
        pyramid_request,
        group_update_service,
        CreateGroupAPISchema,
        GroupUpsertContext,
        group,
    ):
        context = GroupUpsertContext(group, pyramid_request)

        CreateGroupAPISchema.return_value.validate.return_value = {"name": "Dingdong"}

        views.upsert(context, pyramid_request)

        group_update_service.update.assert_called_once_with(
            group, **{"name": "Dingdong", "description": "", "groupid": None}
        )

    def test_it_creates_group_context_from_updated_group(
        self,
        pyramid_request,
        GroupContext,
        group_update_service,
        group,
        GroupUpsertContext,
    ):
        context = GroupUpsertContext(group, pyramid_request)
        group_update_service.update.return_value = group

        views.upsert(context, pyramid_request)

        GroupContext.assert_called_with(group, pyramid_request)

    def test_it_returns_updated_group_formatted_with_presenter(
        self,
        pyramid_request,
        GroupContext,
        GroupJSONPresenter,
        group,
        GroupUpsertContext,
    ):
        context = GroupUpsertContext(group, pyramid_request)
        views.upsert(context, pyramid_request)

        GroupJSONPresenter.assert_called_once_with(GroupContext.return_value)
        GroupJSONPresenter.return_value.asdict.assert_called_once_with(
            expand=["organization", "scopes"]
        )

    @pytest.fixture
    def create(self, patch):
        return patch("h.views.api.groups.create")

    @pytest.fixture
    def group_user(self, factories):
        return factories.User()

    @pytest.fixture
    def group(self, factories, group_user):
        return factories.Group(creator=group_user)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        # Add a nominal json_body so that _json_payload() parsing of
        # it doesn't raise
        pyramid_request.json_body = {}
        return pyramid_request

    @pytest.fixture
    def GroupUpsertContext(self):
        def context_factory(group, request):
            return mock.create_autospec(
                traversal.GroupUpsertContext, instance=True, group=group
            )

        return context_factory


@pytest.mark.usefixtures("group_members_service", "user_service")
class TestAddMember(object):
    def test_it_adds_user_from_request_params_to_group(
        self, group, user, pyramid_request, group_members_service
    ):
        views.add_member(group, pyramid_request)

        group_members_service.member_join.assert_called_once_with(group, user.userid)

    def test_it_returns_HTTPNoContent_when_add_member_is_successful(
        self, group, pyramid_request
    ):
        resp = views.add_member(group, pyramid_request)

        assert isinstance(resp, HTTPNoContent)

    def test_it_raises_HTTPNotFound_with_mismatched_user_and_group_authorities(
        self, factories, pyramid_request
    ):
        group = factories.Group(authority="different_authority.com")

        with pytest.raises(HTTPNotFound):
            views.add_member(group, pyramid_request)

    def test_it_raises_HTTPNotFound_with_non_existent_user(
        self, group, pyramid_request, user_service
    ):

        user_service.fetch.return_value = None

        pyramid_request.matchdict["userid"] = "some_user"

        with pytest.raises(HTTPNotFound):
            views.add_member(group, pyramid_request)

    def test_it_raises_HTTPNotFound_if_userid_malformed(
        self, group, pyramid_request, user_service
    ):

        user_service.fetch.side_effect = ValueError("nope")

        pyramid_request.matchdict["userid"] = "invalidformat@wherever"

        with pytest.raises(HTTPNotFound):  # view handles ValueError and raises NotFound
            views.add_member(group, pyramid_request)

    def test_it_fetches_user_from_the_request_params(
        self, group, user, pyramid_request, user_service
    ):
        views.add_member(group, pyramid_request)

        user_service.fetch.assert_called_once_with(user.userid)

    @pytest.fixture
    def group(self, factories):
        return factories.Group(authority="example.com")

    @pytest.fixture
    def user(self, factories):
        return factories.User(authority="example.com")

    @pytest.fixture
    def pyramid_request(self, pyramid_request, group, user):
        pyramid_request.matchdict["userid"] = user.userid
        pyramid_request.matchdict["pubid"] = group.pubid
        return pyramid_request

    @pytest.fixture
    def user_service(self, pyramid_config, user):
        service = mock.create_autospec(UserService, spec_set=True, instance=True)
        service.fetch.return_value = user
        pyramid_config.register_service(service, name="user")
        return service


@pytest.mark.usefixtures("authenticated_userid", "group_members_service")
class TestRemoveMember(object):
    def test_it_removes_current_user(
        self, shorthand_request, authenticated_userid, group_members_service
    ):
        group = mock.sentinel.group

        views.remove_member(group, shorthand_request)

        group_members_service.member_leave.assert_called_once_with(
            group, authenticated_userid
        )

    def test_it_returns_no_content(self, shorthand_request):
        group = mock.sentinel.group

        response = views.remove_member(group, shorthand_request)

        assert isinstance(response, HTTPNoContent)

    def test_it_fails_with_username(self, username_request):
        group = mock.sentinel.group

        with pytest.raises(HTTPBadRequest):
            views.remove_member(group, username_request)

    @pytest.fixture
    def shorthand_request(self, pyramid_request):
        pyramid_request.matchdict["userid"] = "me"
        return pyramid_request

    @pytest.fixture
    def username_request(self, pyramid_request):
        pyramid_request.matchdict["userid"] = "bob"
        return pyramid_request

    @pytest.fixture
    def authenticated_userid(self, pyramid_config):
        userid = "acct:bob@example.org"
        pyramid_config.testing_securitypolicy(userid)
        return userid


@pytest.fixture
def anonymous_request(pyramid_request):
    pyramid_request.user = None
    return pyramid_request


@pytest.fixture
def GroupJSONPresenter(patch):
    return patch("h.views.api.groups.GroupJSONPresenter")


@pytest.fixture
def GroupsJSONPresenter(patch):
    return patch("h.views.api.groups.GroupsJSONPresenter")


@pytest.fixture
def GroupContext(patch):
    return patch("h.views.api.groups.GroupContext")


@pytest.fixture
def CreateGroupAPISchema(patch):
    return patch("h.views.api.groups.CreateGroupAPISchema")


@pytest.fixture
def UpdateGroupAPISchema(patch):
    return patch("h.views.api.groups.UpdateGroupAPISchema")


@pytest.fixture
def group_create_service(pyramid_config):
    service = mock.create_autospec(GroupCreateService, spec_set=True, instance=True)
    pyramid_config.register_service(service, name="group_create")
    return service


@pytest.fixture
def group_update_service(pyramid_config):
    service = mock.create_autospec(GroupUpdateService, spec_set=True, instance=True)
    pyramid_config.register_service(service, name="group_update")
    return service


@pytest.fixture
def group_service(pyramid_config):
    service = mock.create_autospec(GroupService, spec_set=True, instance=True)
    service.fetch.return_value = None
    pyramid_config.register_service(service, name="group")
    return service


@pytest.fixture
def group_members_service(pyramid_config):
    service = mock.create_autospec(GroupMembersService, spec_set=True, instance=True)
    pyramid_config.register_service(service, name="group_members")
    return service


@pytest.fixture
def group_links_service(pyramid_config):
    svc = mock.create_autospec(GroupLinksService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name="group_links")
    return svc


@pytest.fixture
def group_list_service(pyramid_config):
    svc = mock.create_autospec(GroupListService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name="group_list")
    return svc
