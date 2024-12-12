import logging
from unittest.mock import PropertyMock, call, create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPConflict, HTTPNoContent, HTTPNotFound

import h.views.api.group_members as views
from h import presenters
from h.models import GroupMembership
from h.schemas.base import ValidationError
from h.security import Permission
from h.security.identity import Identity, LongLivedGroup, LongLivedMembership
from h.services.group_members import ConflictError
from h.traversal import (
    AddGroupMembershipContext,
    EditGroupMembershipContext,
    GroupContext,
    GroupMembershipContext,
)
from h.views.api.exceptions import PayloadError


class TestListMembersLegacy:
    def test_it(
        self,
        context,
        pyramid_request,
        GroupMembershipJSONPresenter,
        group_members_service,
        caplog,
    ):
        pyramid_request.headers["User-Agent"] = sentinel.user_agent
        pyramid_request.headers["Referer"] = sentinel.referer
        group_members_service.get_memberships.return_value = [
            sentinel.membership_1,
            sentinel.membership_2,
        ]

        presenter_instances = GroupMembershipJSONPresenter.side_effect = [
            create_autospec(
                presenters.GroupMembershipJSONPresenter, instance=True, spec_set=True
            ),
            create_autospec(
                presenters.GroupMembershipJSONPresenter, instance=True, spec_set=True
            ),
        ]

        response = views.list_members_legacy(context, pyramid_request)

        assert caplog.messages == [
            f"list_members_legacy() was called. User-Agent: {sentinel.user_agent}, Referer: {sentinel.referer}, pubid: {context.group.pubid}"
        ]
        group_members_service.get_memberships.assert_called_once_with(context.group)
        assert GroupMembershipJSONPresenter.call_args_list == [
            call(pyramid_request, sentinel.membership_1),
            call(pyramid_request, sentinel.membership_2),
        ]
        presenter_instances[0].asdict.assert_called_once_with()
        presenter_instances[1].asdict.assert_called_once_with()
        assert response == [
            presenter_instances[0].asdict.return_value,
            presenter_instances[1].asdict.return_value,
        ]

    @pytest.fixture
    def context(self, factories):
        return create_autospec(
            GroupContext, instance=True, spec_set=True, group=factories.Group()
        )


class TestListMembers:
    def test_it(
        self,
        context,
        pyramid_request,
        GroupMembershipJSONPresenter,
        group_members_service,
        PaginationQueryParamsSchema,
        validate_query_params,
    ):
        pyramid_request.params = validate_query_params.return_value = {
            "page[number]": 3,
            "page[size]": 2,
        }
        group_members_service.get_memberships.return_value = [
            sentinel.membership_1,
            sentinel.membership_2,
        ]
        presenter_instances = GroupMembershipJSONPresenter.side_effect = [
            create_autospec(
                presenters.GroupMembershipJSONPresenter, instance=True, spec_set=True
            ),
            create_autospec(
                presenters.GroupMembershipJSONPresenter, instance=True, spec_set=True
            ),
        ]

        response = views.list_members(context, pyramid_request)

        PaginationQueryParamsSchema.assert_called_once_with()
        validate_query_params.assert_called_once_with(
            PaginationQueryParamsSchema.return_value, pyramid_request.params
        )
        group_members_service.count_memberships.assert_called_once_with(context.group)
        group_members_service.get_memberships.assert_called_once_with(
            context.group, offset=4, limit=2
        )
        assert GroupMembershipJSONPresenter.call_args_list == [
            call(pyramid_request, sentinel.membership_1),
            call(pyramid_request, sentinel.membership_2),
        ]
        presenter_instances[0].asdict.assert_called_once_with()
        presenter_instances[1].asdict.assert_called_once_with()
        assert response == {
            "meta": {
                "page": {"total": group_members_service.count_memberships.return_value}
            },
            "data": [
                presenter_instances[0].asdict.return_value,
                presenter_instances[1].asdict.return_value,
            ],
        }

    @pytest.fixture
    def context(self, factories):
        return create_autospec(
            GroupContext, instance=True, spec_set=True, group=factories.Group()
        )


class TestGetMember:
    def test_it(self, context, pyramid_request, GroupMembershipJSONPresenter):
        response = views.get_member(context, pyramid_request)

        GroupMembershipJSONPresenter.assert_called_once_with(
            pyramid_request, sentinel.membership
        )
        GroupMembershipJSONPresenter.return_value.asdict.assert_called_once_with()
        assert response == GroupMembershipJSONPresenter.return_value.asdict.return_value

    @pytest.fixture
    def context(self):
        return GroupMembershipContext(
            group=sentinel.group, user=sentinel.user, membership=sentinel.membership
        )


class TestRemoveMember:
    def test_it(self, context, pyramid_request, group_members_service):
        response = views.remove_member(context, pyramid_request)

        group_members_service.member_leave.assert_called_once_with(
            context.group, context.user.userid
        )
        assert isinstance(response, HTTPNoContent)

    @pytest.fixture
    def context(self, factories):
        group = factories.Group.build()
        user = factories.User.build()
        membership = GroupMembership(group=group, user=user)
        return GroupMembershipContext(group=group, user=user, membership=membership)


@pytest.mark.usefixtures("group_members_service")
class TestAddMember:
    def test_it(
        self,
        pyramid_request,
        group_members_service,
        context,
        GroupMembershipJSONPresenter,
        EditGroupMembershipAPISchema,
    ):
        response = views.add_member(context, pyramid_request)

        EditGroupMembershipAPISchema.assert_called_once_with()
        EditGroupMembershipAPISchema.return_value.validate.assert_called_once_with(
            sentinel.json_body
        )
        group_members_service.member_join.assert_called_once_with(
            context.group, context.user.userid, roles=sentinel.roles
        )
        GroupMembershipJSONPresenter.assert_called_once_with(
            pyramid_request, group_members_service.member_join.return_value
        )
        GroupMembershipJSONPresenter.return_value.asdict.assert_called_once_with()
        assert response == GroupMembershipJSONPresenter.return_value.asdict.return_value

    def test_it_with_no_request_body(
        self,
        pyramid_request,
        group_members_service,
        context,
        EditGroupMembershipAPISchema,
    ):
        pyramid_request.body = b""

        views.add_member(context, pyramid_request)

        EditGroupMembershipAPISchema.assert_not_called()
        group_members_service.member_join.assert_called_once_with(
            context.group, context.user.userid, roles=None
        )

    def test_it_when_a_conflicting_membership_already_exists(
        self, pyramid_request, group_members_service, context
    ):
        group_members_service.member_join.side_effect = ConflictError(
            "test_error_message"
        )

        with pytest.raises(HTTPConflict, match="^test_error_message$"):
            views.add_member(context, pyramid_request)

    def test_it_errors_if_the_request_isnt_valid_JSON(
        self, context, pyramid_request, mocker
    ):
        value_error = ValueError()
        mocker.patch.object(
            type(pyramid_request),
            "json_body",
            PropertyMock(side_effect=value_error),
            create=True,
        )

        with pytest.raises(PayloadError) as exc_info:
            views.add_member(context, pyramid_request)

        assert exc_info.value.__cause__ == value_error

    def test_it_with_authority_mismatch(self, pyramid_request, context):
        context.group.authority = "other"

        with pytest.raises(HTTPNotFound):
            views.add_member(context, pyramid_request)

    @pytest.fixture
    def context(self, factories):
        group = factories.Group.build()
        user = factories.User.build(authority=group.authority)
        return AddGroupMembershipContext(group=group, user=user, new_roles=None)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.body = sentinel.body
        pyramid_request.json_body = sentinel.json_body
        return pyramid_request

    @pytest.fixture
    def EditGroupMembershipAPISchema(self, EditGroupMembershipAPISchema):
        EditGroupMembershipAPISchema.return_value.validate.return_value = {
            "roles": sentinel.roles
        }
        return EditGroupMembershipAPISchema


class TestEditMember:
    def test_it(
        self,
        context,
        pyramid_request,
        EditGroupMembershipAPISchema,
        GroupMembershipJSONPresenter,
        caplog,
        mocker,
    ):
        has_permission = mocker.spy(pyramid_request, "has_permission")

        response = views.edit_member(context, pyramid_request)

        EditGroupMembershipAPISchema.return_value.validate.assert_called_once_with(
            sentinel.json_body
        )
        assert context.new_roles == sentinel.new_roles
        has_permission.assert_called_once_with(Permission.Group.MEMBER_EDIT, context)
        assert context.membership.roles == sentinel.new_roles
        GroupMembershipJSONPresenter.assert_called_once_with(
            pyramid_request, context.membership
        )
        assert response == GroupMembershipJSONPresenter.return_value.asdict.return_value
        assert caplog.messages == [
            f"Changed group membership roles: {context.membership!r} (previous roles were: {sentinel.old_roles!r})",
        ]

    def test_noop(self, context, pyramid_request, EditGroupMembershipAPISchema, caplog):
        EditGroupMembershipAPISchema.return_value.validate.return_value["roles"] = (
            sentinel.old_roles
        )

        views.edit_member(context, pyramid_request)

        assert not caplog.messages

    def test_user_changing_own_role(self, context, pyramid_request, pyramid_config):
        context.user = pyramid_request.user
        identity = create_autospec(Identity, instance=True, spec_set=True)
        identity.user.memberships = [
            create_autospec(
                LongLivedMembership,
                instance=True,
                group=create_autospec(LongLivedGroup, instance=True, id="other"),
            ),
            create_autospec(
                LongLivedMembership,
                instance=True,
                group=create_autospec(
                    LongLivedGroup, instance=True, id=context.group.id
                ),
            ),
        ]
        pyramid_config.testing_securitypolicy(permissive=True, identity=identity)

        views.edit_member(context, pyramid_request)

        assert identity.user.memberships[1].roles == sentinel.new_roles

    def test_it_errors_if_the_user_doesnt_have_permission(
        self, context, pyramid_request, pyramid_config
    ):
        pyramid_config.testing_securitypolicy(permissive=False)

        with pytest.raises(HTTPNotFound):
            views.edit_member(context, pyramid_request)

    def test_it_errors_if_the_request_isnt_valid_JSON(
        self, context, pyramid_request, mocker
    ):
        value_error = ValueError()
        mocker.patch.object(
            type(pyramid_request),
            "json_body",
            PropertyMock(side_effect=value_error),
            create=True,
        )

        with pytest.raises(PayloadError) as exc_info:
            views.edit_member(context, pyramid_request)

        assert exc_info.value.__cause__ == value_error

    def test_it_errors_if_the_request_is_invalid(
        self, context, pyramid_request, EditGroupMembershipAPISchema
    ):
        EditGroupMembershipAPISchema.return_value.validate.side_effect = ValidationError

        with pytest.raises(ValidationError):
            views.edit_member(context, pyramid_request)

    @pytest.fixture
    def context(self, factories):
        group = factories.Group.build()
        user = factories.User.build(authority=group.authority)
        membership = GroupMembership(group=group, user=user, roles=sentinel.old_roles)
        return EditGroupMembershipContext(
            group=group, user=user, membership=membership, new_roles=None
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.json_body = sentinel.json_body
        return pyramid_request

    @pytest.fixture
    def EditGroupMembershipAPISchema(self, EditGroupMembershipAPISchema):
        EditGroupMembershipAPISchema.return_value.validate.return_value = {
            "roles": sentinel.new_roles
        }
        return EditGroupMembershipAPISchema

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config):
        pyramid_config.testing_securitypolicy(permissive=True)
        return pyramid_config


@pytest.fixture
def caplog(caplog):
    caplog.set_level(logging.INFO)
    return caplog


@pytest.fixture(autouse=True)
def EditGroupMembershipAPISchema(mocker):
    return mocker.patch(
        "h.views.api.group_members.EditGroupMembershipAPISchema",
        autospec=True,
        spec_set=True,
    )


@pytest.fixture(autouse=True)
def PaginationQueryParamsSchema(mocker):
    return mocker.patch(
        "h.views.api.group_members.PaginationQueryParamsSchema",
        autospec=True,
        spec_set=True,
    )


@pytest.fixture(autouse=True)
def validate_query_params(mocker):
    return mocker.patch(
        "h.views.api.group_members.validate_query_params", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def GroupMembershipJSONPresenter(mocker):
    return mocker.patch(
        "h.views.api.group_members.GroupMembershipJSONPresenter",
        autospec=True,
        spec_set=True,
    )
