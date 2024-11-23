from h.models import GroupMembership
from h.presenters.group_membership_json import GroupMembershipJSONPresenter


class TestGroupMembershipJSONPresenter:
    def test_it(self, factories):
        user = factories.User.build()
        group = factories.Group.build()
        membership = GroupMembership(user=user, group=group)

        json = GroupMembershipJSONPresenter(membership).asdict()

        assert json == {
            "authority": group.authority,
            "userid": user.userid,
            "username": user.username,
            "display_name": user.display_name,
            "roles": membership.roles,
        }
