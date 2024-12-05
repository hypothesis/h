from datetime import datetime

import pytest

from h.models import GroupMembership
from h.presenters.group_membership_json import GroupMembershipJSONPresenter


class TestGroupMembershipJSONPresenter:
    def test_it(self, user, group, membership, pyramid_request, pyramid_config):
        pyramid_config.testing_securitypolicy(permissive=False)

        json = GroupMembershipJSONPresenter(pyramid_request, membership).asdict()

        assert json == {
            "authority": group.authority,
            "userid": user.userid,
            "username": user.username,
            "display_name": user.display_name,
            "roles": membership.roles,
            "actions": [],
            "created": "1970-01-01T00:00:00.000000+00:00",
            "updated": "1970-01-01T00:00:01.000000+00:00",
        }

    def test_it_with_permissive_securitypolicy(
        self, user, group, membership, pyramid_request, pyramid_config
    ):
        pyramid_config.testing_securitypolicy(permissive=True)

        json = GroupMembershipJSONPresenter(pyramid_request, membership).asdict()

        assert json == {
            "authority": group.authority,
            "userid": user.userid,
            "username": user.username,
            "display_name": user.display_name,
            "roles": membership.roles,
            "actions": [
                "delete",
                "updates.roles.member",
                "updates.roles.moderator",
                "updates.roles.admin",
                "updates.roles.owner",
            ],
            "created": "1970-01-01T00:00:00.000000+00:00",
            "updated": "1970-01-01T00:00:01.000000+00:00",
        }

    def test_it_with_no_created_or_updated_times(self, membership, pyramid_request):
        membership.created = None
        membership.updated = None

        json = GroupMembershipJSONPresenter(pyramid_request, membership).asdict()

        assert json["created"] is None
        assert json["updated"] is None

    @pytest.fixture
    def user(self, factories):
        return factories.User.build()

    @pytest.fixture
    def group(self, factories):
        return factories.Group.build()

    @pytest.fixture
    def membership(self, user, group):
        return GroupMembership(
            user=user,
            group=group,
            created=datetime(1970, 1, 1, 0, 0, 0),
            updated=datetime(1970, 1, 1, 0, 0, 1),
        )
