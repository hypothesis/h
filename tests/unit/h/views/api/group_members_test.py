import logging
from unittest.mock import PropertyMock, call, create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound

import h.views.api.group_members as views
from h import presenters
from h.models import GroupMembership
from h.schemas.base import ValidationError
from h.traversal import GroupContext, GroupMembershipContext
from h.views.api.exceptions import PayloadError


class TestListMembers:
    def test_it(self, context, pyramid_request, GroupMembershipJSONPresenter):
        context.group.memberships = [sentinel.membership_1, sentinel.membership_2]
        presenter_instances = GroupMembershipJSONPresenter.side_effect = [
            create_autospec(
                presenters.GroupMembershipJSONPresenter, instance=True, spec_set=True
            ),
            create_autospec(
                presenters.GroupMembershipJSONPresenter, instance=True, spec_set=True
            ),
        ]

        response = views.list_members(context, pyramid_request)

        assert GroupMembershipJSONPresenter.call_args_list == [
            call(sentinel.membership_1),
            call(sentinel.membership_2),
        ]
        presenter_instances[0].asdict.assert_called_once_with()
        presenter_instances[1].asdict.assert_called_once_with()
        assert response == [
            presenter_instances[0].asdict.return_value,
            presenter_instances[1].asdict.return_value,
        ]

    @pytest.fixture
    def context(self):
        return create_autospec(
            GroupContext, instance=True, spec_set=True, group=sentinel.group
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
    def test_it(self, pyramid_request, group_members_service, context):
        response = views.add_member(context, pyramid_request)

        group_members_service.member_join.assert_called_once_with(
            context.group, context.user.userid
        )
        assert isinstance(response, HTTPNoContent)

    def test_it_with_authority_mismatch(self, pyramid_request, context):
        context.group.authority = "other"

        with pytest.raises(HTTPNotFound):
            views.add_member(context, pyramid_request)

    @pytest.fixture
    def context(self, factories):
        group = factories.Group.build()
        user = factories.User.build(authority=group.authority)
        return GroupMembershipContext(group=group, user=user, membership=None)


class TestEditMember:
    def test_it(
        self,
        context,
        pyramid_request,
        EditGroupMembershipAPISchema,
        GroupMembershipJSONPresenter,
        caplog,
    ):
        response = views.edit_member(context, pyramid_request)

        EditGroupMembershipAPISchema.return_value.validate.assert_called_once_with(
            sentinel.json_body
        )
        assert context.membership.roles == sentinel.new_roles
        GroupMembershipJSONPresenter.assert_called_once_with(context.membership)
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

        return GroupMembershipContext(group=group, user=user, membership=membership)

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
    def caplog(self, caplog):
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
def GroupMembershipJSONPresenter(mocker):
    return mocker.patch(
        "h.views.api.group_members.GroupMembershipJSONPresenter",
        autospec=True,
        spec_set=True,
    )
