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

    GROUP_PAGES = (
        ("POST", "/admin/groups/delete/{pubid}", 302),
        ("GET", "/admin/groups/{pubid}", 200),
    )

    @pytest.mark.usefixtures("with_logged_in_admin")
    @pytest.mark.parametrize("method,url_template,success_code", GROUP_PAGES)
    def test_group_end_points_accessible_by_admin(
        self, app, group, method, url_template, success_code
    ):
        url = url_template.format(pubid=group.pubid)

        app.request(url, method=method, status=success_code)

    @pytest.mark.usefixtures("with_logged_in_staff_member")
    @pytest.mark.parametrize("method,url_template,success_code", GROUP_PAGES)
    def test_group_end_points_accessible_by_staff(
        self, app, group, method, url_template, success_code
    ):
        url = url_template.format(pubid=group.pubid)

        app.request(url, method=method, status=success_code)

    @pytest.mark.usefixtures("with_logged_in_user")
    @pytest.mark.parametrize("method,url_template,_", GROUP_PAGES)
    def test_group_end_points_not_accessible_by_regular_user(
        self, app, group, method, url_template, _
    ):
        url = url_template.format(pubid=group.pubid)

        app.request(url, method=method, status=404)

    @pytest.fixture
    def group(self, factories, db_session):
        # Without an org `views.admin.groups:GroupEditViews._update_appstruct`
        # fails
        group = factories.Group(organization=factories.Organization())
        db_session.commit()
        return group
