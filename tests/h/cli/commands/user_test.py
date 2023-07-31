from unittest import mock

import pytest

from h import models
from h.cli.commands import user as user_cli


class TestAddCommand:
    def test_it_adds_user_with_default_authority(
        self, cli, cliconfig, user_signup_service
    ):
        result = cli.invoke(
            user_cli.add,
            [
                "--username",
                "admin",
                "--email",
                "admin@localhost",
                "--password",
                "admin",
            ],
            obj=cliconfig,
        )

        assert not result.exit_code

        user_signup_service.signup.assert_called_with(
            username="admin",
            email="admin@localhost",
            password="admin",
            require_activation=False,
        )

    def test_it_adds_user_with_specific_authority(
        self, cli, cliconfig, user_signup_service
    ):
        result = cli.invoke(
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
            obj=cliconfig,
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
    def test_it_adds_admin(self, cli, cliconfig, non_admin_user, db_session):
        result = cli.invoke(
            user_cli.admin, ["--on", non_admin_user.username], obj=cliconfig
        )

        assert not result.exit_code

        user = db_session.query(models.User).get(non_admin_user.id)
        assert user.admin

    def test_it_adds_admin_by_default(self, cli, cliconfig, non_admin_user, db_session):
        result = cli.invoke(user_cli.admin, [non_admin_user.username], obj=cliconfig)

        assert not result.exit_code

        user = db_session.query(models.User).get(non_admin_user.id)
        assert user.admin

    def test_it_adds_admin_with_specific_authority(
        self, cli, cliconfig, non_admin_user, db_session
    ):
        non_admin_user.authority = "partner.org"
        db_session.flush()

        result = cli.invoke(
            user_cli.admin,
            ["--authority", "partner.org", non_admin_user.username],
            obj=cliconfig,
        )

        assert not result.exit_code

        user = db_session.query(models.User).get(non_admin_user.id)
        assert user.admin

    def test_it_removes_admin(self, cli, cliconfig, admin_user, db_session):
        result = cli.invoke(
            user_cli.admin, ["--off", admin_user.username], obj=cliconfig
        )

        assert not result.exit_code

        user = db_session.query(models.User).get(admin_user.id)
        assert not user.admin

    def test_it_removes_admin_with_specific_authority(
        self, cli, cliconfig, admin_user, db_session
    ):
        admin_user.authority = "partner.org"

        result = cli.invoke(
            user_cli.admin,
            ["--off", "--authority", "partner.org", admin_user.username],
            obj=cliconfig,
        )

        assert not result.exit_code

        user = db_session.query(models.User).get(admin_user.id)
        assert not user.admin

    def test_it_errors_when_user_could_not_be_found(
        self, cli, cliconfig, non_admin_user, db_session
    ):
        result = cli.invoke(
            user_cli.admin, [f"bogus_{non_admin_user.username}"], obj=cliconfig
        )

        assert result.exit_code == 1
        user = db_session.query(models.User).get(non_admin_user.id)
        assert not user.admin

    def test_it_errors_when_user_with_specific_authority_could_not_be_found(
        self, cli, cliconfig, non_admin_user, db_session
    ):
        result = cli.invoke(
            user_cli.admin,
            ["--authority", "foo.com", non_admin_user.username],
            obj=cliconfig,
        )

        assert result.exit_code == 1
        user = db_session.query(models.User).get(non_admin_user.id)
        assert not user.admin

    @pytest.fixture
    def admin_user(self, factories):
        return factories.User(admin=True)

    @pytest.fixture
    def non_admin_user(self, factories):
        return factories.User(admin=False)


class TestPasswordCommand:
    def test_it_changes_password(
        self, cli, cliconfig, user, db_session, user_password_service
    ):
        result = cli.invoke(
            user_cli.password, [user.username, "--password", "newpass"], obj=cliconfig
        )

        assert not result.exit_code

        user = db_session.query(models.User).get(user.id)
        user_password_service.update_password.assert_called_once_with(user, "newpass")

    def test_it_changes_password_with_specific_authority(
        self, cli, cliconfig, user, db_session, user_password_service
    ):
        user.authority = "partner.org"
        db_session.flush()

        result = cli.invoke(
            user_cli.password,
            ["--authority", "partner.org", user.username, "--password", "newpass"],
            obj=cliconfig,
        )

        assert not result.exit_code

        user = db_session.query(models.User).get(user.id)
        user_password_service.update_password.assert_called_once_with(user, "newpass")

    def test_it_errors_when_user_could_not_be_found(
        self, cli, cliconfig, user_password_service
    ):
        result = cli.invoke(
            user_cli.password,
            ["bogus_username", "--password", "newpass"],
            obj=cliconfig,
        )

        assert result.exit_code == 1

        user_password_service.update_password.assert_not_called()

    def test_it_errors_when_user_with_specific_authority_could_not_be_found(
        self, cli, cliconfig, user, user_password_service
    ):
        result = cli.invoke(
            user_cli.password,
            ["--authority", "foo.com", user.username, "--password", "newpass"],
            obj=cliconfig,
        )

        assert result.exit_code == 1

        user_password_service.update_password.assert_not_called()

    @pytest.fixture
    def user(self, factories):
        return factories.User()


class TestDeleteUserCommand:
    def test_it_deletes_user(self, cli, cliconfig, user, user_delete_service):
        result = cli.invoke(user_cli.delete, [user.username], obj=cliconfig)

        assert not result.exit_code
        user_delete_service.delete.assert_called_once_with(user)

    def test_it_deletes_user_with_specific_authority(
        self, cli, cliconfig, user, user_delete_service
    ):
        user.authority = "partner.org"

        result = cli.invoke(
            user_cli.delete,
            ["--authority", "partner.org", user.username],
            obj=cliconfig,
        )

        assert not result.exit_code
        user_delete_service.delete.assert_called_once_with(user)

    def test_it_errors_when_user_could_not_be_found(
        self, cli, cliconfig, user_delete_service
    ):
        result = cli.invoke(user_cli.delete, ["bogus_username"], obj=cliconfig)

        assert result.exit_code == 1
        user_delete_service.delete.assert_not_called()

    def test_it_errors_when_user_with_specific_authority_could_not_be_found(
        self, cli, cliconfig, user, user_delete_service
    ):
        result = cli.invoke(
            user_cli.delete, ["--authority", "foo.com", user.username], obj=cliconfig
        )

        assert result.exit_code == 1
        user_delete_service.delete.assert_not_called()

    @pytest.fixture
    def user(self, factories):
        return factories.User()


@pytest.fixture
def cliconfig(pyramid_config, pyramid_request):  # pylint:disable=unused-argument
    pyramid_request.tm = mock.Mock()
    return {"bootstrap": mock.Mock(return_value=pyramid_request)}
