import re
from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound

from h.exceptions import InvalidUserId
from h.traversal.group_membership import (
    AddGroupMembershipContext,
    EditGroupMembershipContext,
    GroupMembershipContext,
    group_membership_api_factory,
)


@pytest.mark.usefixtures("group_service", "user_service", "group_members_service")
class TestGroupMembershipAPIFactory:
    @pytest.mark.parametrize("request_method", ["GET", "DELETE"])
    def test_get_delete(
        self,
        group_service,
        user_service,
        group_members_service,
        pyramid_request,
        request_method,
    ):
        pyramid_request.method = request_method

        context = group_membership_api_factory(pyramid_request)

        group_service.fetch.assert_called_once_with(sentinel.pubid)
        user_service.fetch.assert_called_once_with(sentinel.userid)
        group_members_service.get_membership.assert_called_once_with(
            group_service.fetch.return_value, user_service.fetch.return_value
        )
        assert isinstance(context, GroupMembershipContext)
        assert context.group == group_service.fetch.return_value
        assert context.user == user_service.fetch.return_value
        assert context.membership == group_members_service.get_membership.return_value

    def test_post(
        self, group_service, user_service, group_members_service, pyramid_request
    ):
        pyramid_request.method = "POST"

        context = group_membership_api_factory(pyramid_request)

        group_service.fetch.assert_called_once_with(sentinel.pubid)
        user_service.fetch.assert_called_once_with(sentinel.userid)
        group_members_service.get_membership.assert_not_called()
        assert isinstance(context, AddGroupMembershipContext)
        assert context.group == group_service.fetch.return_value
        assert context.user == user_service.fetch.return_value
        assert context.new_roles is None

    def test_patch(
        self, group_service, user_service, group_members_service, pyramid_request
    ):
        pyramid_request.method = "PATCH"

        context = group_membership_api_factory(pyramid_request)

        group_service.fetch.assert_called_once_with(sentinel.pubid)
        user_service.fetch.assert_called_once_with(sentinel.userid)
        group_members_service.get_membership.assert_called_once_with(
            group_service.fetch.return_value, user_service.fetch.return_value
        )
        assert isinstance(context, EditGroupMembershipContext)
        assert context.group == group_service.fetch.return_value
        assert context.user == user_service.fetch.return_value
        assert context.membership == group_members_service.get_membership.return_value
        assert context.new_roles is None

    @pytest.mark.parametrize("request_method", ["GET", "POST", "PATCH", "DELETE"])
    def test_when_no_matching_group(
        self, group_service, pyramid_request, request_method
    ):
        pyramid_request.method = request_method
        group_service.fetch.return_value = None

        with pytest.raises(HTTPNotFound, match=r"Group not found: sentinel\.pubid"):
            group_membership_api_factory(pyramid_request)

    @pytest.mark.parametrize("request_method", ["GET", "POST", "PATCH", "DELETE"])
    def test_when_no_matching_user(self, user_service, pyramid_request, request_method):
        pyramid_request.method = request_method
        user_service.fetch.return_value = None

        with pytest.raises(HTTPNotFound, match=r"User not found: sentinel\.userid"):
            group_membership_api_factory(pyramid_request)

    @pytest.mark.parametrize("request_method", ["GET", "POST", "PATCH", "DELETE"])
    def test_when_invalid_userid(self, user_service, pyramid_request, request_method):
        pyramid_request.method = request_method
        user_service.fetch.side_effect = InvalidUserId(sentinel.userid)

        with pytest.raises(HTTPNotFound, match=r"User not found: sentinel\.userid"):
            group_membership_api_factory(pyramid_request)

    @pytest.mark.parametrize("request_method", ["GET", "PATCH", "DELETE"])
    def test_when_no_matching_membership(
        self, group_members_service, pyramid_request, request_method
    ):
        pyramid_request.method = request_method
        group_members_service.get_membership.return_value = None

        with pytest.raises(
            HTTPNotFound,
            match=re.escape("Membership not found: (sentinel.pubid, sentinel.userid)"),
        ):
            group_membership_api_factory(pyramid_request)

    @pytest.mark.parametrize("request_method", ["GET", "POST", "PATCH", "DELETE"])
    def test_me_alias(
        self, pyramid_config, pyramid_request, user_service, request_method
    ):
        pyramid_request.method = request_method
        pyramid_config.testing_securitypolicy(userid=sentinel.userid)
        pyramid_request.matchdict["userid"] = "me"

        group_membership_api_factory(pyramid_request)

        user_service.fetch.assert_called_once_with(sentinel.userid)

    @pytest.mark.parametrize("request_method", ["GET", "POST", "PATCH", "DELETE"])
    def test_me_alias_when_not_authenticated(self, pyramid_request, request_method):
        pyramid_request.method = request_method
        pyramid_request.matchdict["userid"] = "me"

        with pytest.raises(HTTPNotFound, match="User not found: me"):
            group_membership_api_factory(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["pubid"] = sentinel.pubid
        pyramid_request.matchdict["userid"] = sentinel.userid
        return pyramid_request
