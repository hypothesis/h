# -*- coding: utf-8 -*-

import mock
import pytest

from h import models
from h.cli.commands import authclient as authclient_cli


class TestAddCommand(object):

    def test_it_creates_an_authclient(self, cli, cliconfig, db_session):
        authclient = self._add_authclient(cli, cliconfig, db_session)
        assert authclient

    def test_it_prints_the_client_id_and_secret(self, cli, cliconfig, db_session, echo):
        authclient = self._add_authclient(cli, cliconfig, db_session)
        echo.assert_called_with('OAuth client for publisher.org created\n' +
                                'Client ID: {}\n'.format(authclient.id) +
                                'Client Secret: {}'.format(authclient.secret))

    def _add_authclient(self, cli, cliconfig, db_session):
        result = cli.invoke(authclient_cli.add,
                            [u'--name', 'Publisher', u'--authority', 'publisher.org'],
                            obj=cliconfig)

        assert result.exit_code == 0

        authclient = db_session.query(models.AuthClient).filter(
                   models.AuthClient.authority == 'publisher.org').first()
        return authclient


class TestSecretCommand(object):
    def test_it_prints_the_client_id_and_secret(self, authclient, cli, cliconfig, echo):
        result = cli.invoke(authclient_cli.secret, [u'partner.org'], obj=cliconfig)

        assert result.exit_code == 0

        echo.assert_called_with('ID: {}\nSecret: {}'.format(authclient.id, authclient.secret))

    @pytest.fixture
    def authclient(self, db_session, factories):
        authclient = models.AuthClient(name='Partner', authority='partner.org')
        db_session.add(authclient)
        db_session.flush()
        return authclient


@pytest.fixture
def cliconfig(pyramid_config, pyramid_request):
    pyramid_request.tm = mock.Mock()
    return {'bootstrap': mock.Mock(return_value=pyramid_request)}


@pytest.fixture
def echo(patch):
    echo = patch('h.cli.commands.authclient.click.echo')
    return echo
