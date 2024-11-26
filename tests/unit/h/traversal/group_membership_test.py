import re
from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound

from h.exceptions import InvalidUserId
from h.traversal.group_membership import (
    GroupMembershipContext,
    group_membership_api_factory,
)


@pytest.mark.usefixtures("group_service", "user_service", "group_members_service")
class TestGroupMembershipAPIFactory:
    def test_it(
        self, group_service, user_service, group_members_service, pyramid_request
    ):
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

    def test_when_no_matching_group(self, group_service, pyramid_request):
        group_service.fetch.return_value = None

        with pytest.raises(HTTPNotFound, match="Group not found: sentinel.pubid"):
            group_membership_api_factory(pyramid_request)

    def test_when_no_matching_user(self, user_service, pyramid_request):
        user_service.fetch.return_value = None

        with pytest.raises(HTTPNotFound, match="User not found: sentinel.userid"):
            group_membership_api_factory(pyramid_request)

    def test_when_invalid_userid(self, user_service, pyramid_request):
        user_service.fetch.side_effect = InvalidUserId(sentinel.userid)

        with pytest.raises(HTTPNotFound, match="User not found: sentinel.userid"):
            group_membership_api_factory(pyramid_request)

    def test_when_no_matching_membership(self, group_members_service, pyramid_request):
        group_members_service.get_membership.return_value = None

        with pytest.raises(
            HTTPNotFound,
            match=re.escape("Membership not found: (sentinel.pubid, sentinel.userid)"),
        ):
            group_membership_api_factory(pyramid_request)

    def test_me_alias(self, pyramid_config, pyramid_request, user_service):
        pyramid_config.testing_securitypolicy(userid=sentinel.userid)
        pyramid_request.matchdict["userid"] = "me"

        group_membership_api_factory(pyramid_request)

        user_service.fetch.assert_called_once_with(sentinel.userid)

    def test_me_alias_when_not_authenticated(self, pyramid_request):
        pyramid_request.matchdict["userid"] = "me"

        with pytest.raises(HTTPNotFound, match="User not found: me"):
            group_membership_api_factory(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["pubid"] = sentinel.pubid
        pyramid_request.matchdict["userid"] = sentinel.userid
        return pyramid_request
