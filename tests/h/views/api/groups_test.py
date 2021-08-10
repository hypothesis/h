from unittest import mock

import pytest
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPConflict,
    HTTPNoContent,
    HTTPNotFound,
)

from h.traversal.group import GroupContext
from h.views.api import groups as views


@pytest.mark.usefixtures("group_list_service", "group_links_service")
class TestGetGroups:
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

    @pytest.mark.parametrize(
        "expand",
        ([], ["organization"], ["organization", "scopes"]),
    )
    def test_returns_dicts_from_presenter(
        self,
        anonymous_request,
        open_groups,
        group_list_service,
        GroupsJSONPresenter,
        expand,
    ):
        for param in expand:
            anonymous_request.GET.add("expand", param)

        group_list_service.request_groups.return_value = open_groups

        result = views.groups(anonymous_request)

        GroupsJSONPresenter.assert_called_once_with(open_groups, anonymous_request)
        GroupsJSONPresenter.return_value.asdicts.assert_called_once_with(expand=expand)
        assert result == GroupsJSONPresenter.return_value.asdicts.return_value

    @pytest.fixture
    def open_groups(self, factories):
        return [factories.OpenGroup(), factories.OpenGroup()]

    @pytest.fixture
    def anonymous_request(self, pyramid_request):
        pyramid_request.user = None
        return pyramid_request


@pytest.mark.usefixtures(
    "CreateGroupAPISchema", "group_service", "group_create_service"
)
class TestCreateGroup:
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
        self, pyramid_request, group_service, factories
    ):
        # Return a different pre-existing group when we search by id
        group_service.fetch.return_value = factories.Group(
            authority_provided_id="different_id", authority="example.com"
        )

        with pytest.raises(HTTPConflict, match="group with groupid.*already exists"):
            views.create(pyramid_request)

    def test_it_creates_group_context_from_created_group(
        self, pyramid_request, factories, group_create_service, GroupJSONPresenter
    ):
        group = factories.Group()
        group_create_service.create_private_group.return_value = group

        result = views.create(pyramid_request)

        GroupJSONPresenter.assert_called_once_with(group, pyramid_request)
        GroupJSONPresenter.return_value.asdict.assert_called_once_with(
            expand=["organization", "scopes"]
        )
        assert result == GroupJSONPresenter.return_value.asdict.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request, factories):
        # Add a nominal json_body so that _json_payload() parsing of
        # it doesn't raise
        pyramid_request.json_body = {}
        pyramid_request.user = factories.User()
        return pyramid_request


class TestReadGroup:
    def test_it(self, context, pyramid_request, GroupJSONPresenter):
        pyramid_request.params["expand"] = "organization"

        result = views.read(context, pyramid_request)

        GroupJSONPresenter.assert_called_once_with(context.group, pyramid_request)
        GroupJSONPresenter.return_value.asdict.assert_called_once_with(["organization"])
        assert result == GroupJSONPresenter.return_value.asdict.return_value


@pytest.mark.usefixtures("group_service", "group_update_service")
class TestUpdateGroup:
    def test_it_inits_group_update_schema(
        self, pyramid_request, context, UpdateGroupAPISchema
    ):
        views.update(context, pyramid_request)

        UpdateGroupAPISchema.return_value.validate.assert_called_once_with({})

    def test_it_passes_request_params_to_group_update_service(
        self, context, pyramid_request, UpdateGroupAPISchema, group_update_service
    ):
        patch_payload = {"name": "My Group", "description": "How about that?"}
        UpdateGroupAPISchema.return_value.validate.return_value = patch_payload

        views.update(context, pyramid_request)

        group_update_service.update.assert_called_once_with(
            context.group, **patch_payload
        )

    def test_it_raises_HTTPConflict_on_duplicate(
        self, pyramid_request, context, group_service, factories
    ):
        # Return a different pre-existing group when we search by id
        group_service.fetch.return_value = factories.Group(
            authority_provided_id="different_id", authority=context.group.authority
        )

        with pytest.raises(HTTPConflict, match="group with groupid.*already exists"):
            views.update(context, pyramid_request)

    def test_it_does_not_raise_HTTPConflict_if_duplicate_is_same_group(
        self, pyramid_request, context, group_service
    ):
        group_service.fetch.return_value = context.group

        views.update(context, pyramid_request)

    def test_it_creates_group_context_from_updated_group(
        self, pyramid_request, context, group_update_service, GroupJSONPresenter
    ):
        group_update_service.update.return_value = context.group

        result = views.update(context, pyramid_request)

        GroupJSONPresenter.assert_called_with(context.group, pyramid_request)
        GroupJSONPresenter.return_value.asdict.assert_called_once_with(
            expand=["organization", "scopes"]
        )
        assert result == GroupJSONPresenter.return_value.asdict.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request, factories):
        # Add a nominal json_body so that _json_payload() parsing of
        # it doesn't raise
        pyramid_request.json_body = {}
        pyramid_request.user = factories.User()
        return pyramid_request

    @pytest.fixture(autouse=True)
    def UpdateGroupAPISchema(self, patch):
        return patch("h.views.api.groups.UpdateGroupAPISchema")


@pytest.mark.usefixtures(
    "CreateGroupAPISchema", "group_service", "group_update_service"
)
class TestUpsertGroup:
    def test_it_proxies_to_create_if_group_empty(
        self, context, pyramid_request, groups_create
    ):
        context.group = None

        res = views.upsert(context, pyramid_request)

        groups_create.assert_called_once_with(pyramid_request)
        assert res == groups_create.return_value

    def test_it_does_not_proxy_to_create_if_group_extant(
        self, context, pyramid_request, groups_create
    ):
        views.upsert(context, pyramid_request)

        assert not groups_create.call_count

    def test_it_validates_against_group_update_schema_if_group_extant(
        self, context, pyramid_request, CreateGroupAPISchema
    ):
        pyramid_request.json_body = {"name": "Rename Group"}

        views.upsert(context, pyramid_request)

        CreateGroupAPISchema.return_value.validate.assert_called_once_with(
            {"name": "Rename Group"}
        )

    def test_it_raises_HTTPConflict_on_duplicate(
        self, context, pyramid_request, group_service, factories
    ):
        # Return a different pre-existing group when we search by id
        group_service.fetch.return_value = factories.Group(
            authority_provided_id="different_id", authority=context.group.authority
        )

        with pytest.raises(HTTPConflict, match="group with groupid.*already exists"):
            views.upsert(context, pyramid_request)

    def test_it_does_not_raise_HTTPConflict_if_duplicate_is_same_group(
        self, context, pyramid_request, group_service
    ):
        group_service.fetch.return_value = context.group

        views.upsert(context, pyramid_request)

    def test_it_proxies_to_update_service_with_injected_defaults(
        self, context, pyramid_request, group_update_service, CreateGroupAPISchema
    ):
        CreateGroupAPISchema.return_value.validate.return_value = {"name": "Dingdong"}

        views.upsert(context, pyramid_request)

        group_update_service.update.assert_called_once_with(
            context.group, **{"name": "Dingdong", "description": "", "groupid": None}
        )

    def test_it_returns_updated_group_formatted_with_presenter(
        self, context, pyramid_request, group_update_service, GroupJSONPresenter
    ):
        group_update_service.update.return_value = context.group

        result = views.upsert(context, pyramid_request)

        GroupJSONPresenter.assert_called_with(context.group, pyramid_request)
        GroupJSONPresenter.return_value.asdict.assert_called_once_with(
            expand=["organization", "scopes"]
        )
        assert result == GroupJSONPresenter.return_value.asdict.return_value

    @pytest.fixture
    def groups_create(self, patch):
        return patch("h.views.api.groups.create")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        # Add a nominal json_body so that _json_payload() parsing of
        # it doesn't raise
        pyramid_request.json_body = {}
        return pyramid_request


class TestReadMembers:
    def test_it_returns_formatted_users_from_group(
        self, context, factories, pyramid_request, UserJSONPresenter
    ):
        context.group.members = [
            factories.User.build(),
            factories.User.build(),
            factories.User.build(),
        ]

        views.read_members(context, pyramid_request)

        assert UserJSONPresenter.call_count == len(context.group.members)

    @pytest.fixture
    def UserJSONPresenter(self, patch):
        return patch("h.views.api.groups.UserJSONPresenter")


@pytest.mark.usefixtures("group_members_service", "user_service")
class TestAddMember:
    def test_it_adds_user_from_request_params_to_group(
        self, context, user, pyramid_request, group_members_service
    ):
        views.add_member(context, pyramid_request)

        group_members_service.member_join.assert_called_once_with(
            context.group, user.userid
        )

    def test_it_returns_HTTPNoContent_when_add_member_is_successful(
        self, context, pyramid_request
    ):
        resp = views.add_member(context, pyramid_request)

        assert isinstance(resp, HTTPNoContent)

    def test_it_raises_HTTPNotFound_with_mismatched_user_and_group_authorities(
        self, context, pyramid_request
    ):
        context.group.authority = "different_authority.com"

        with pytest.raises(HTTPNotFound):
            views.add_member(context, pyramid_request)

    def test_it_raises_HTTPNotFound_with_non_existent_user(
        self, context, pyramid_request, user_service
    ):
        user_service.fetch.return_value = None

        pyramid_request.matchdict["userid"] = "some_user"

        with pytest.raises(HTTPNotFound):
            views.add_member(context, pyramid_request)

    def test_it_raises_HTTPNotFound_if_userid_malformed(
        self, context, pyramid_request, user_service
    ):
        user_service.fetch.side_effect = ValueError("nope")

        pyramid_request.matchdict["userid"] = "invalidformat@wherever"

        with pytest.raises(HTTPNotFound):  # view handles ValueError and raises NotFound
            views.add_member(context, pyramid_request)

    def test_it_fetches_user_from_the_request_params(
        self, context, user, pyramid_request, user_service
    ):
        views.add_member(context, pyramid_request)

        user_service.fetch.assert_called_once_with(user.userid)

    @pytest.fixture
    def user(self, factories):
        return factories.User(authority="example.com")

    @pytest.fixture
    def pyramid_request(self, pyramid_request, context, user):
        pyramid_request.matchdict["userid"] = user.userid
        pyramid_request.matchdict["pubid"] = context.group.pubid
        return pyramid_request

    @pytest.fixture
    def user_service(self, user_service, user):
        user_service.fetch.return_value = user

        return user_service


@pytest.mark.usefixtures("authenticated_userid", "group_members_service")
class TestRemoveMember:
    def test_it_removes_current_user(
        self, context, shorthand_request, authenticated_userid, group_members_service
    ):

        views.remove_member(context, shorthand_request)

        group_members_service.member_leave.assert_called_once_with(
            context.group, authenticated_userid
        )

    def test_it_returns_no_content(self, context, shorthand_request):
        response = views.remove_member(context, shorthand_request)

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
def group_service(group_service):
    group_service.fetch.return_value = None

    return group_service


@pytest.fixture
def CreateGroupAPISchema(patch):
    return patch("h.views.api.groups.CreateGroupAPISchema")


@pytest.fixture(autouse=True)
def GroupsJSONPresenter(patch):
    return patch("h.views.api.groups.GroupsJSONPresenter")


@pytest.fixture(autouse=True)
def GroupJSONPresenter(patch):
    return patch("h.views.api.groups.GroupJSONPresenter")


@pytest.fixture
def context(factories):
    return GroupContext(group=factories.Group(creator=factories.User()))
