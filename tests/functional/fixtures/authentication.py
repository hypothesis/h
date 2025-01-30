import pytest

__all__ = (
    "login_user",
    "user",
    "with_logged_in_admin",
    "with_logged_in_staff_member",
    "with_logged_in_user",
)


@pytest.fixture
def user(factories):
    return factories.User()


@pytest.fixture
def login_user(db_session, app, user):
    def login_user(staff=False, admin=False):  # noqa: FBT002
        # This is the hash for `pass` used below
        user.password = "$2b$12$21I1LjTlGJmLXzTDrQA8gusckjHEMepTmLY5WN3Kx8hSaqEEKj9V6"  # noqa: S105
        user.staff = staff
        user.admin = admin
        db_session.commit()

        login_page = app.get("/login")
        login_page.form["username"] = user.username
        login_page.form["password"] = "pass"  # noqa: S105
        login_page.form.submit()

    return login_user


@pytest.fixture
def with_logged_in_user(login_user):
    login_user()


@pytest.fixture
def with_logged_in_staff_member(login_user):
    login_user(staff=True)


@pytest.fixture
def with_logged_in_admin(login_user):
    login_user(admin=True)
