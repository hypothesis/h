from unittest import mock

import pytest

from h import models
from h.cli.commands import authclient as authclient_cli


class TestAddCommand:
    def test_it_creates_a_public_authclient(self, cli, cliconfig, db_session):
        (authclient, _) = self._add_authclient(
            cli, cliconfig, db_session, type_="public"
        )

        assert authclient.authority == "publisher.org"
        assert authclient.name == "Publisher"
        assert authclient.secret is None

    def test_it_creates_a_confidential_authclient(
        self, cli, cliconfig, db_session, patch
    ):
        token_urlsafe = patch("h.cli.commands.authclient.token_urlsafe")
        token_urlsafe.return_value = "fixed-secret-token"

        (authclient, _) = self._add_authclient(
            cli, cliconfig, db_session, type_="confidential"
        )

        assert authclient.authority == "publisher.org"
        assert authclient.name == "Publisher"
        assert authclient.secret == "fixed-secret-token"

    def test_it_prints_the_id_for_public_client(self, cli, cliconfig, db_session):
        (authclient, output) = self._add_authclient(
            cli, cliconfig, db_session, type_="public"
        )
        expected_id_and_secret = f"Client ID: {authclient.id}"
        assert expected_id_and_secret in output

    def test_it_prints_the_id_and_secret_for_confidential_client(
        self, cli, cliconfig, db_session
    ):
        (authclient, output) = self._add_authclient(
            cli, cliconfig, db_session, type_="confidential"
        )
        expected_id_and_secret = (
            f"Client ID: {authclient.id}\nClient Secret: {authclient.secret}"
        )
        assert expected_id_and_secret in output

    def test_it_creates_an_authclient_with_grant_type(self, cli, cliconfig, db_session):
        result = cli.invoke(
            authclient_cli.add,
            [
                "--name",
                "AuthCode",
                "--authority",
                "example.org",
                "--type",
                "public",
                "--grant-type",
                "authorization_code",
                "--redirect-uri",
                "http://localhost:5000/app.html",
            ],
            obj=cliconfig,
        )

        assert not result.exit_code

        authclient = (
            db_session.query(models.AuthClient)
            .filter(models.AuthClient.authority == "example.org")
            .first()
        )
        assert authclient.grant_type.value == "authorization_code"
        assert authclient.redirect_uri == "http://localhost:5000/app.html"

    def _add_authclient(self, cli, cliconfig, db_session, type_):
        result = cli.invoke(
            authclient_cli.add,
            ["--name", "Publisher", "--authority", "publisher.org", "--type", type_],
            obj=cliconfig,
        )

        assert not result.exit_code

        authclient = (
            db_session.query(models.AuthClient)
            .filter(models.AuthClient.authority == "publisher.org")
            .first()
        )
        return (authclient, result.output)


@pytest.fixture
def cliconfig(pyramid_request):
    pyramid_request.tm = mock.Mock()
    return {"bootstrap": mock.Mock(return_value=pyramid_request)}
