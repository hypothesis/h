import pytest


class TestAdminPermissions:
    PAGES = (
        # URL, accessible by role.Staff?
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

    @pytest.mark.parametrize("url", (page[0] for page in PAGES))
    def test_not_accessible_by_regular_user(self, app, url, user):
        self.login(app, user)

        res = app.get(url, expect_errors=True)

        assert res.status_code == 404

    @pytest.mark.parametrize("url", (page[0] for page in PAGES))
    def test_accessible_by_admin(self, app, url, admin_user):
        self.login(app, admin_user)

        res = app.get(url)

        assert res.status_code == 200

    @pytest.mark.parametrize("url,accessible", PAGES)
    def test_accessible_by_staff(self, app, url, accessible, staff_user):
        self.login(app, staff_user)

        res = app.get(url, expect_errors=not accessible)

        assert res.status_code == 200 if accessible else 404

    @pytest.fixture
    def user(self, db_session, factories):
        # Password is 'pass'
        return factories.User(
            password="$2b$12$21I1LjTlGJmLXzTDrQA8gusckjHEMepTmLY5WN3Kx8hSaqEEKj9V6"
        )

    @pytest.fixture
    def staff_user(self, user, db_session):
        user.staff = True
        db_session.commit()

        return user

    @pytest.fixture
    def admin_user(self, user, db_session):
        user.admin = True
        db_session.commit()

        return user

    def login(self, app, user):
        login_page = app.get("/login")
        login_page.form["username"] = user.username
        login_page.form["password"] = "pass"
        login_page.form.submit()
