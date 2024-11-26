import logging
from unittest import mock

import pytest
from sqlalchemy import select

from h.models import GroupMembership, GroupMembershipRoles, User
from h.services.group_members import GroupMembersService, group_members_factory


class TestGetMembership:
    def test_it(self, group_members_service, factories, db_session):
        group = factories.Group.build()
        user = factories.User.build()
        membership = GroupMembership(group=group, user=user)
        db_session.add(membership)

        result = group_members_service.get_membership(group, user)

        assert result == membership

    def test_it_when_theres_no_matching_membership(
        self, group_members_service, factories
    ):
        group = factories.Group()
        user = factories.User()

        result = group_members_service.get_membership(group, user)

        assert result is None


class TestGetMemberships:
    def test_it(self, group_members_service, db_session, factories):
        group, other_group = factories.Group.build_batch(size=2)
        users = factories.User.build_batch(size=2)
        memberships = [GroupMembership(group=group, user=user) for user in users]
        db_session.add_all(
            [*memberships, GroupMembership(group=other_group, user=users[0])]
        )

        assert list(group_members_service.get_memberships(group)) == sorted(
            memberships, key=lambda membership: membership.user.username
        )

    def test_roles(self, group_members_service, db_session, factories):
        group = factories.Group.build()
        admins = factories.User.build_batch(size=2)
        moderator = factories.User.build()
        memberships = [
            GroupMembership(group=group, user=user, roles=[GroupMembershipRoles.ADMIN])
            for user in admins
        ]
        db_session.add_all(
            [
                *memberships,
                GroupMembership(
                    group=group, user=moderator, roles=[GroupMembershipRoles.MODERATOR]
                ),
            ]
        )

        assert list(
            group_members_service.get_memberships(
                group, roles=[GroupMembershipRoles.ADMIN]
            )
        ) == sorted(memberships, key=lambda membership: membership.user.username)

    def test_multiple_roles(self, group_members_service, db_session, factories):
        group = factories.Group.build()
        admin = factories.User.build()
        moderator = factories.User.build()
        member = factories.User.build()
        memberships = [
            GroupMembership(
                group=group, user=admin, roles=[GroupMembershipRoles.ADMIN]
            ),
            GroupMembership(
                group=group, user=moderator, roles=[GroupMembershipRoles.MODERATOR]
            ),
        ]
        db_session.add_all(
            [
                *memberships,
                GroupMembership(
                    group=group, user=member, roles=[GroupMembershipRoles.MEMBER]
                ),
            ]
        )

        assert list(
            group_members_service.get_memberships(
                group,
                roles=[GroupMembershipRoles.ADMIN, GroupMembershipRoles.MODERATOR],
            )
        ) == sorted(memberships, key=lambda membership: membership.user.username)


class TestMemberJoin:
    def test_it_adds_user_to_group(
        self, group_members_service, factories, caplog, db_session
    ):
        caplog.set_level(logging.INFO)
        user = factories.User()
        group = factories.Group()
        group_members_service.member_join(group, user.userid)

        membership = db_session.scalars(
            select(GroupMembership)
            .where(GroupMembership.user == user)
            .where(GroupMembership.group == group)
        ).one_or_none()
        assert membership
        assert caplog.messages == [f"Added group membership: {membership!r}"]

    def test_it_is_idempotent(self, group_members_service, factories):
        user = factories.User()
        group = factories.Group()
        group_members_service.member_join(group, user.userid)
        group_members_service.member_join(group, user.userid)

        assert group.members.count(user) == 1

    def test_it_publishes_join_event(self, group_members_service, factories, publish):
        group = factories.Group()
        user = factories.User()

        group_members_service.member_join(group, user.userid)

        publish.assert_called_once_with("group-join", group.pubid, user.userid)


class TestMemberLeave:
    def test_it_removes_user_from_group(
        self, group_members_service, factories, db_session, caplog
    ):
        caplog.set_level(logging.INFO)
        group, other_group = factories.Group.create_batch(size=2)
        user, other_user = factories.User.create_batch(size=2)
        membership = GroupMembership(group=group, user=user)
        db_session.add_all(
            [
                membership,
                GroupMembership(group=other_group, user=user),
                GroupMembership(group=group, user=other_user),
            ]
        )

        group_members_service.member_leave(group, user.userid)

        assert user not in group.members
        assert user in other_group.members
        assert other_user in group.members
        assert caplog.messages == [f"Deleted group membership: {membership!r}"]

    def test_it_does_nothing_if_the_user_isnt_a_member(
        self, group_members_service, factories, publish
    ):
        group = factories.Group()
        user = factories.User()

        group_members_service.member_leave(group, user.userid)

        publish.assert_not_called()

    def test_it_publishes_leave_event(self, group_members_service, factories, publish):
        group = factories.Group()
        new_member = factories.User(memberships=[GroupMembership(group=group)])

        group_members_service.member_leave(group, new_member.userid)

        publish.assert_called_once_with("group-leave", group.pubid, new_member.userid)


class TestAddMembers:
    def test_it_adds_users_in_userids(self, factories, group_members_service):
        group = factories.OpenGroup()
        users = [factories.User(), factories.User()]
        userids = [user.userid for user in users]

        group_members_service.add_members(group, userids)

        assert all(user in group.members for user in users)

    def test_it_does_not_remove_existing_members(
        self, factories, group_members_service
    ):
        group = factories.Group()
        existing_member = factories.User()
        group.memberships.append(GroupMembership(user=existing_member))

        group_members_service.add_members(group, [factories.User().userid])

        assert existing_member in group.members


class TestUpdateMembers:
    def test_it_adds_users_in_userids(self, factories, group_members_service):
        group = factories.OpenGroup()  # no members at outset
        new_members = (factories.User(), factories.User())

        group_members_service.update_members(
            group, [user.userid for user in new_members]
        )

        assert group.members == new_members

    def test_it_removes_members_not_present_in_userids(
        self, db_session, factories, group_members_service, creator
    ):
        group = factories.Group(
            creator=creator,
            memberships=[
                GroupMembership(user=factories.User()),
                GroupMembership(user=factories.User()),
            ],
        )

        group_members_service.update_members(group, [])

        assert not db_session.scalars(
            select(GroupMembership).where(GroupMembership.group == group)
        ).all()

    def test_it_does_not_remove_members_present_in_userids(
        self, factories, group_members_service, publish
    ):
        group = factories.OpenGroup()  # no members at outset
        new_members = [factories.User(), factories.User()]
        group.memberships.append(GroupMembership(user=new_members[0]))
        group.memberships.append(GroupMembership(user=new_members[1]))

        group_members_service.update_members(
            group, [user.userid for user in group.members]
        )

        assert new_members[0] in group.members
        assert new_members[1] in group.members
        publish.assert_not_called()

    def test_it_proxies_to_member_join_and_leave(
        self, factories, group_members_service
    ):
        group_members_service.member_join = mock.Mock()
        group_members_service.member_leave = mock.Mock()

        group = factories.OpenGroup()
        new_members = [factories.User(), factories.User()]
        group.memberships.append(GroupMembership(user=new_members[0]))

        group_members_service.update_members(group, [new_members[1].userid])

        group_members_service.member_join.assert_called_once_with(
            group, new_members[1].userid
        )
        assert sorted(group_members_service.member_leave.call_args_list) == sorted(
            [
                mock.call(group, new_members[0].userid),
            ]
        )

    def test_it_does_not_add_duplicate_members(self, factories, group_members_service):
        # test for idempotency
        group = factories.OpenGroup()
        new_member = factories.User()

        group_members_service.update_members(
            group, [new_member.userid, new_member.userid]
        )

        assert group.members == (new_member,)


@pytest.mark.usefixtures("user_service")
class TestFactory:
    def test_returns_groups_service(self, pyramid_request):
        group_members_service = group_members_factory(None, pyramid_request)

        assert isinstance(group_members_service, GroupMembersService)

    def test_provides_request_db_as_session(self, pyramid_request):
        group_members_service = group_members_factory(None, pyramid_request)

        assert group_members_service.db == pyramid_request.db

    def test_wraps_user_service_as_user_fetcher(self, pyramid_request, user_service):
        group_members_service = group_members_factory(None, pyramid_request)

        group_members_service.user_fetcher("foo")

        user_service.fetch.assert_called_once_with("foo")

    def test_provides_realtime_publisher_as_publish(self, patch, pyramid_request):
        pyramid_request.realtime = mock.Mock(spec_set=["publish_user"])
        session = patch("h.services.group_members.session")
        group_members_service = group_members_factory(None, pyramid_request)

        group_members_service.publish("group-join", "abc123", "theresa")

        session.model.assert_called_once_with(pyramid_request)
        pyramid_request.realtime.publish_user.assert_called_once_with(
            {
                "type": "group-join",
                "session_model": session.model.return_value,
                "userid": "theresa",
                "group": "abc123",
            }
        )


@pytest.fixture
def usr_group_members_service(db_session):
    def fetch(userid):
        # One doesn't want to couple to the user fetching service but
        # we do want to be able to fetch user models for internal
        # module behavior tests
        return db_session.query(User).filter_by(userid=userid).one_or_none()

    return fetch


@pytest.fixture
def publish():
    return mock.Mock(spec_set=[])


@pytest.fixture
def group_members_service(db_session, usr_group_members_service, publish):
    return GroupMembersService(db_session, usr_group_members_service, publish=publish)


@pytest.fixture
def creator(factories):
    return factories.User(username="group_creator")
