import pytest

from h.models import GroupMembership, GroupMembershipRoles

pytestmark = pytest.mark.usefixtures("init_elasticsearch")


class TestGroupSearchController:
    @pytest.mark.usefixtures("with_logged_in_user")
    @pytest.mark.xfail(
        reason="See https://github.com/hypothesis/product-backlog/issues/109"
    )
    def test_group_page_includes_referrer_tag(self, app, user_owned_group):
        """
        The group read page should include a referrer tag.

        When a logged-in user who is a member of the group visits the group's page,
        the page should include a `<meta name="referrer" ...` tag that asks the
        browser not to send the path part of the page's URL to third-party servers
        in the Referer header when following links on the page.

        This is because the group's URL is secret - if you have it you can join
        the group.
        """

        response = app.get(f"/groups/{user_owned_group.pubid}/{user_owned_group.slug}")

        assert response.html.head.find(
            "meta", attrs={"name": "referrer"}, content="origin"
        )

    @pytest.mark.parametrize("should_login", (True, False))
    def test_join_page_is_shown_instead_of_search_without_read_permissions(
        self, login_user, app, group, should_login
    ):
        # If you don't have read permissions
        # But you do have join permissions / or you aren't logged in
        # Show the join page
        if should_login:
            login_user()

        response = app.get(f"/groups/{group.pubid}/{group.slug}")

        assert "join-group-form" in str(response.html)

    @pytest.mark.usefixtures("with_logged_in_user")
    def test_404_is_raised_if_you_do_not_have_join_permission(
        self, app, other_authority_group
    ):
        # A user has the JOIN permission if a group is marked as joinable by
        # authority, they are logged in user and in the right authority

        # We use a group in another authority as it means we don't have join
        app.get(
            f"/groups/{other_authority_group.pubid}/{other_authority_group.slug}",
            status=404,
        )

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
        self, app, db_session, factories, user, role
    ):
        group = factories.OpenGroup(
            memberships=[GroupMembership(user=user, roles=[role])]
        )
        db_session.commit()

        response = app.get(f"/groups/{group.pubid}/{group.slug}")

        assert f"http://localhost/groups/{group.pubid}/edit" in str(response.html)

    @pytest.mark.usefixtures("with_logged_in_user")
    @pytest.mark.parametrize("role", [GroupMembershipRoles.MEMBER])
    def test_unauthorized_members_cant_edit_groups(
        self, app, db_session, factories, user, role
    ):
        group = factories.OpenGroup(
            memberships=[GroupMembership(user=user, roles=[role])]
        )
        db_session.commit()

        response = app.get(f"/groups/{group.pubid}/{group.slug}")

        assert f"http://localhost/groups/{group.pubid}/edit" not in str(response.html)

    @pytest.mark.usefixtures("with_logged_in_user")
    def test_non_members_cant_edit_groups(self, app, db_session, factories):
        group = factories.OpenGroup()
        db_session.commit()

        response = app.get(f"/groups/{group.pubid}/{group.slug}")

        assert f"http://localhost/groups/{group.pubid}/edit" not in str(response.html)

    def test_unauthenticated_users_cant_edit_groups(self, app, db_session, factories):
        group = factories.OpenGroup()
        db_session.commit()

        response = app.get(f"/groups/{group.pubid}/{group.slug}")

        assert f"http://localhost/groups/{group.pubid}/edit" not in str(response.html)
