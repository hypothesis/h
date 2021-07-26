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

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def with_logged_in_user(self, login_user):
        login_user()

    @pytest.fixture
    def with_logged_in_staff_member(self, login_user, user):
        user.staff = True

        login_user()

    @pytest.fixture
    def with_logged_in_admin(self, login_user, user):
        user.admin = True

        login_user()

    @pytest.fixture
    def login_user(self, db_session, app, user):
        def login_user():
            # This is the hash for `pass` used below
            user.password = (
                "$2b$12$21I1LjTlGJmLXzTDrQA8gusckjHEMepTmLY5WN3Kx8hSaqEEKj9V6"
            )
            db_session.commit()

            login_page = app.get("/login")
            login_page.form["username"] = user.username
            login_page.form["password"] = "pass"
            login_page.form.submit()

        return login_user
