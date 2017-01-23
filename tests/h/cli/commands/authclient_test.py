# -*- coding: utf-8 -*-

import mock
import pytest

from h import models
from h.cli.commands import authclient as authclient_cli


class TestAddCommand(object):

    def test_it_creates_an_authclient(self, cli, cliconfig, db_session):
        (authclient, _) = self._add_authclient(cli, cliconfig, db_session)

        assert authclient.authority == 'publisher.org'
        assert authclient.name == 'Publisher'

    def test_it_prints_the_client_id_and_secret(self, cli, cliconfig, db_session):
        (authclient, output) = self._add_authclient(cli, cliconfig, db_session)
        expected_id_and_secret = ('Client ID: {}\n'.format(authclient.id) +
                                  'Client Secret: {}'.format(authclient.secret))
        assert expected_id_and_secret in output

    def _add_authclient(self, cli, cliconfig, db_session):
        result = cli.invoke(authclient_cli.add,
                            [u'--name', 'Publisher', u'--authority', 'publisher.org'],
                            obj=cliconfig)

        assert result.exit_code == 0

        authclient = db_session.query(models.AuthClient).filter(
                   models.AuthClient.authority == 'publisher.org').first()
        return (authclient, result.output)


@pytest.fixture
def cliconfig(pyramid_config, pyramid_request):
    pyramid_request.tm = mock.Mock()
    return {'bootstrap': mock.Mock(return_value=pyramid_request)}
