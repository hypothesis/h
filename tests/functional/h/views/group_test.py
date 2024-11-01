import pytest

from h.models import GroupMembership, GroupMembershipRoles

pytestmark = pytest.mark.usefixtures("init_elasticsearch")


class TestGroupEditController:
    # These permissions tests are a stand-in for testing all functionality of
    # the group edit controller as they all need the same permission. We will
    # just test GET as it's the simplest.
    @pytest.mark.usefixtures("with_logged_in_user")
    @pytest.mark.parametrize(
        "role",
        [
            GroupMembershipRoles.OWNER,
            GroupMembershipRoles.ADMIN,
            GroupMembershipRoles.MODERATOR,
        ],
    )
    def test_authorized_members_can_edit_groups(
        self, app, group, role, db_session, user
    ):
        group.memberships.append(GroupMembership(user=user, roles=[role]))
        db_session.commit()

        app.get(f"/groups/{group.pubid}/edit")

    @pytest.mark.usefixtures("with_logged_in_user")
    @pytest.mark.parametrize(
        "role",
        [GroupMembershipRoles.MEMBER],
    )
    def test_unauthorized_members_cant_edit_groups(
        self, app, group, role, db_session, user
    ):
        group.memberships.append(GroupMembership(user=user, roles=[role]))
        db_session.commit()

        app.get(f"/groups/{group.pubid}/edit", status=404)

    @pytest.mark.usefixtures("with_logged_in_user")
    def test_non_members_cant_edit_groups(self, app, group):
        app.get(f"/groups/{group.pubid}/edit", status=404)

    def test_unauthenticated_users_cant_edit_groups(self, app, group):
        app.get(f"/groups/{group.pubid}/edit", status=404)

    @pytest.fixture
    def group(self, factories, db_session):
        group = factories.Group()
        db_session.commit()

        return group
