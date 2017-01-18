# -*- coding: utf-8 -*-

import mock
import pytest

from h import models
from h.cli.commands import publisher as publisher_cli


class TestAddCommand(object):

    def test_it_creates_an_authclient(self, cli, cliconfig, db_session):
        result = cli.invoke(publisher_cli.add,
                            [u'--name', 'Publisher', u'--authority', 'publisher.org'],
                            obj=cliconfig)

        assert result.exit_code == 0

        authclient = db_session.query(models.AuthClient).filter(
                   models.AuthClient.authority == 'publisher.org').first()
        assert authclient

    def test_it_creates_a_publisher_group(self, cli, cliconfig, group_service, signup_service):
        result = cli.invoke(publisher_cli.add,
                            [u'--name', 'Publisher', u'--authority', 'publisher.org'],
                            obj=cliconfig)

        assert result.exit_code == 0

        creator_id = signup_service.signup.return_value.userid
        group_service.create.assert_called_with(name=u'Publisher',
                                                authority=u'publisher.org',
                                                userid=creator_id,
                                                type_='publisher')


class TestSecretCommand(object):
    def test_it_prints_the_client_id_and_secret(self, authclient, cli, cliconfig, echo):
        result = cli.invoke(publisher_cli.secret, [u'partner.org'], obj=cliconfig)

        assert result.exit_code == 0

        echo.assert_called_with('ID: {}\nSecret: {}'.format(authclient.id, authclient.secret))

    @pytest.fixture
    def authclient(self, db_session, factories):
        authclient = models.AuthClient(name='Partner', authority='partner.org')
        db_session.add(authclient)
        db_session.flush()
        return authclient


@pytest.fixture
def group_service(pyramid_config):
    group_service = mock.Mock(spec_set=['create'])
    return group_service


@pytest.fixture
def signup_service(pyramid_config):
    signup_service = mock.Mock(spec_set=['signup'])
    return signup_service


@pytest.fixture
def cliconfig(pyramid_config, pyramid_request, group_service, signup_service):
    pyramid_config.register_service(group_service, name='group')
    pyramid_config.register_service(signup_service, name='user_signup')
    pyramid_request.tm = mock.Mock()
    return {'bootstrap': mock.Mock(return_value=pyramid_request)}


@pytest.fixture
def echo(patch):
    echo = patch('h.cli.commands.publisher.click.echo')
    return echo
