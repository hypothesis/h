# -*- coding: utf-8 -*-

import mock
import pytest

from h import models
from h.cli.commands import authclient as authclient_cli


class TestAddCommand(object):

    def test_it_creates_a_public_authclient(self, cli, cliconfig, db_session):
        (authclient, _) = self._add_authclient(cli, cliconfig, db_session, type_=u'public')

        assert authclient.authority == 'publisher.org'
        assert authclient.name == 'Publisher'
        assert authclient.secret is None

    def test_it_creates_a_confidential_authclient(self, cli, cliconfig, db_session, patch):
        token_urlsafe = patch('h.cli.commands.authclient.token_urlsafe')
        token_urlsafe.return_value = u'fixed-secret-token'

        (authclient, _) = self._add_authclient(cli, cliconfig, db_session, type_=u'confidential')

        assert authclient.authority == 'publisher.org'
        assert authclient.name == 'Publisher'
        assert authclient.secret == 'fixed-secret-token'

    def test_it_prints_the_id_for_public_client(self, cli, cliconfig, db_session):
        (authclient, output) = self._add_authclient(cli, cliconfig, db_session, type_=u'public')
        expected_id_and_secret = 'Client ID: {}'.format(authclient.id)
        assert expected_id_and_secret in output

    def test_it_prints_the_id_and_secret_for_confidential_client(self, cli, cliconfig, db_session):
        (authclient, output) = self._add_authclient(cli, cliconfig, db_session, type_=u'confidential')
        expected_id_and_secret = ('Client ID: {}\n'.format(authclient.id) +
                                  'Client Secret: {}'.format(authclient.secret))
        assert expected_id_and_secret in output

    def _add_authclient(self, cli, cliconfig, db_session, type_):
        result = cli.invoke(authclient_cli.add,
                            [u'--name', u'Publisher', u'--authority', u'publisher.org', u'--type', type_],
                            obj=cliconfig)

        assert result.exit_code == 0

        authclient = db_session.query(models.AuthClient).filter(
                   models.AuthClient.authority == u'publisher.org').first()
        return (authclient, result.output)


@pytest.fixture
def cliconfig(pyramid_config, pyramid_request):
    pyramid_request.tm = mock.Mock()
    return {'bootstrap': mock.Mock(return_value=pyramid_request)}
