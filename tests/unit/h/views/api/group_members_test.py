from unittest.mock import call, create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound

import h.views.api.group_members as views
from h import presenters
from h.models import GroupMembership
from h.traversal import GroupContext, GroupMembershipContext


class TestReadMembers:
    def test_it(self, context, pyramid_request, UserJSONPresenter):
        context.group.members = [sentinel.member_1, sentinel.member_2]
        presenter_instances = UserJSONPresenter.side_effect = [
            create_autospec(presenters.UserJSONPresenter, instance=True, spec_set=True),
            create_autospec(presenters.UserJSONPresenter, instance=True, spec_set=True),
        ]

        response = views.list_members(context, pyramid_request)

        assert UserJSONPresenter.call_args_list == [
            call(sentinel.member_1),
            call(sentinel.member_2),
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
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict = {"userid": sentinel.userid}
        return pyramid_request

    @pytest.fixture
    def context(self, factories):
        group = factories.Group.build()
        user = factories.User.build(authority=group.authority)
        return GroupMembershipContext(group=group, user=user, membership=None)


@pytest.fixture(autouse=True)
def UserJSONPresenter(mocker):
    return mocker.patch(
        "h.views.api.group_members.UserJSONPresenter", autospec=True, spec_set=True
    )
