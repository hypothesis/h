import pytest


class TestAdminPermissions:
    PAGES = (
        # (URL, accessible by role.Staff?)
        ("/admin/", True),
        ("/admin/admins", False),
        ("/admin/badge", False),
        ("/admin/features", False),
        ("/admin/groups", True),
        ("/admin/mailer", True),
        ("/admin/nipsa", False),
        ("/admin/oauthclients", False),
        ("/admin/organizations", True),
        ("/admin/staff", False),
        ("/admin/users", True),
        ("/admin/search", False),
    )

    @pytest.mark.usefixtures("with_logged_in_user")
    @pytest.mark.parametrize("url", (page[0] for page in PAGES))
    def test_not_accessible_by_regular_user(self, app, url):
        app.get(url, status=404)

    @pytest.mark.usefixtures("with_logged_in_admin")
    @pytest.mark.parametrize("url", (page[0] for page in PAGES))
    def test_accessible_by_admin(self, app, url):
        app.get(url)

    @pytest.mark.usefixtures("with_logged_in_staff_member")
    @pytest.mark.parametrize("url,accessible", PAGES)
    def test_accessible_by_staff(self, app, url, accessible):
        res = app.get(url, expect_errors=not accessible)

        assert res.status_code == 200 if accessible else 404

    @pytest.mark.usefixtures("with_logged_in_admin")
    def test_admin_group_pages_accessible_by_admins(self, app, group):
        app.request(f"/admin/groups/{group.pubid}", method="GET", status=200)

    @pytest.mark.usefixtures("with_logged_in_staff_member")
    def test_admin_group_pages_accessible_by_staff(self, app, group):
        app.request(f"/admin/groups/{group.pubid}", method="GET", status=200)

    @pytest.mark.usefixtures("with_logged_in_user")
    def test_admin_group_pages_NOT_accessible_by_regular_users(self, app, group):
        app.request(f"/admin/groups/{group.pubid}", method="GET", status=404)

    @pytest.mark.usefixtures("with_logged_in_admin")
    def test_admins_can_use_admin_pages_to_delete_groups(self, app, group):
        response = app.request(f"/admin/groups/{group.pubid}")

        response.forms["delete_group"].submit(status=302)

    @pytest.mark.usefixtures("with_logged_in_staff_member")
    def test_staff_can_use_admin_pages_to_delete_groups(self, app, group):
        response = app.request(f"/admin/groups/{group.pubid}")

        response.forms["delete_group"].submit(status=302)

    @pytest.fixture
    def group(self, factories, db_session):
        # Without an org `views.admin.groups:GroupEditViews._update_appstruct`
        # fails
        group = factories.Group(organization=factories.Organization())
        db_session.commit()
        return group
