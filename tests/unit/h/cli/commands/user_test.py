from unittest import mock

import pytest

from h.cli.commands import user as user_cli
from h.models import User


class TestAddCommand:
    def test_it_adds_user_with_default_authority(self, invoke_cli, user_signup_service):
        result = invoke_cli(
            user_cli.add,
            [
                "--username",
                "admin",
                "--email",
                "admin@localhost",
                "--password",
                "admin",
            ],
        )

        assert not result.exit_code

        user_signup_service.signup.assert_called_with(
            username="admin",
            email="admin@localhost",
            password="admin",
            require_activation=False,
        )

    def test_it_adds_user_with_specific_authority(
        self, invoke_cli, user_signup_service
    ):
        result = invoke_cli(
            user_cli.add,
            [
                "--username",
                "admin",
                "--email",
                "admin@localhost",
                "--password",
                "admin",
                "--authority",
                "publisher.org",
            ],
        )

        assert not result.exit_code

        user_signup_service.signup.assert_called_with(
            username="admin",
            email="admin@localhost",
            password="admin",
            authority="publisher.org",
            require_activation=False,
        )


class TestAdminCommand:
    def test_it_adds_admin(self, invoke_cli, non_admin_user, db_session):
        result = invoke_cli(user_cli.admin, ["--on", non_admin_user.username])

        assert not result.exit_code

        user = db_session.get(User, non_admin_user.id)
        assert user.admin

    def test_it_adds_admin_by_default(self, invoke_cli, non_admin_user, db_session):
        result = invoke_cli(user_cli.admin, [non_admin_user.username])

        assert not result.exit_code

        user = db_session.get(User, non_admin_user.id)
        assert user.admin

    def test_it_adds_admin_with_specific_authority(
        self, invoke_cli, non_admin_user, db_session
    ):
        non_admin_user.authority = "partner.org"
        db_session.flush()

        result = invoke_cli(
            user_cli.admin, ["--authority", "partner.org", non_admin_user.username]
        )

        assert not result.exit_code

        user = db_session.get(User, non_admin_user.id)
        assert user.admin

    def test_it_removes_admin(self, invoke_cli, admin_user, db_session):
        result = invoke_cli(user_cli.admin, ["--off", admin_user.username])

        assert not result.exit_code

        user = db_session.get(User, admin_user.id)
        assert not user.admin

    def test_it_removes_admin_with_specific_authority(
        self, invoke_cli, admin_user, db_session
    ):
        admin_user.authority = "partner.org"

        result = invoke_cli(
            user_cli.admin, ["--off", "--authority", "partner.org", admin_user.username]
        )

        assert not result.exit_code

        user = db_session.get(User, admin_user.id)
        assert not user.admin

    def test_it_errors_when_user_could_not_be_found(
        self, invoke_cli, non_admin_user, db_session
    ):
        result = invoke_cli(user_cli.admin, [f"bogus_{non_admin_user.username}"])

        assert result.exit_code == 1
        user = db_session.get(User, non_admin_user.id)
        assert not user.admin

    def test_it_errors_when_user_with_specific_authority_could_not_be_found(
        self, invoke_cli, non_admin_user, db_session
    ):
        result = invoke_cli(
            user_cli.admin, ["--authority", "foo.com", non_admin_user.username]
        )

        assert result.exit_code == 1
        user = db_session.get(User, non_admin_user.id)
        assert not user.admin

    @pytest.fixture
    def admin_user(self, factories):
        return factories.User(admin=True)

    @pytest.fixture
    def non_admin_user(self, factories):
        return factories.User(admin=False)


class TestPasswordCommand:
    def test_it_changes_password(
        self, invoke_cli, user, db_session, user_password_service
    ):
        result = invoke_cli(user_cli.password, [user.username, "--password", "newpass"])

        assert not result.exit_code

        user = db_session.get(User, user.id)
        user_password_service.update_password.assert_called_once_with(user, "newpass")

    def test_it_changes_password_with_specific_authority(
        self, invoke_cli, user, db_session, user_password_service
    ):
        user.authority = "partner.org"
        db_session.flush()

        result = invoke_cli(
            user_cli.password,
            ["--authority", "partner.org", user.username, "--password", "newpass"],
        )

        assert not result.exit_code

        user = db_session.get(User, user.id)
        user_password_service.update_password.assert_called_once_with(user, "newpass")

    def test_it_errors_when_user_could_not_be_found(
        self, invoke_cli, user_password_service
    ):
        result = invoke_cli(
            user_cli.password, ["bogus_username", "--password", "newpass"]
        )

        assert result.exit_code == 1

        user_password_service.update_password.assert_not_called()

    def test_it_errors_when_user_with_specific_authority_could_not_be_found(
        self, invoke_cli, user, user_password_service
    ):
        result = invoke_cli(
            user_cli.password,
            ["--authority", "foo.com", user.username, "--password", "newpass"],
        )

        assert result.exit_code == 1

        user_password_service.update_password.assert_not_called()

    @pytest.fixture
    def user(self, factories):
        return factories.User()


@pytest.fixture
def invoke_cli(cli, pyramid_request):
    pyramid_request.tm = mock.Mock()

    def invoke_cli(method, args):
        return cli.invoke(
            method, args, obj={"bootstrap": mock.Mock(return_value=pyramid_request)}
        )

    return invoke_cli
