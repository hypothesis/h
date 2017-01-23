# -*- coding: utf-8 -*-

import mock
import pytest

from h.cli.commands import groups as groups_cli


class TestAddCommand(object):

    def test_it_creates_a_publisher_group(self, cli, cliconfig, group_service):
        result = cli.invoke(groups_cli.add_publisher_group,
                            [u'--name', 'Publisher', u'--authority', 'publisher.org',
                             u'--creator', 'admin'],
                            obj=cliconfig)

        assert result.exit_code == 0

        group_service.create.assert_called_with(name=u'Publisher',
                                                authority=u'publisher.org',
                                                userid='acct:admin@publisher.org',
                                                type_='publisher')


@pytest.fixture
def group_service(pyramid_config):
    group_service = mock.Mock(spec_set=['create'])
    return group_service


@pytest.fixture
def cliconfig(pyramid_config, pyramid_request, group_service):
    pyramid_config.register_service(group_service, name='group')
    pyramid_request.tm = mock.Mock()
    return {'bootstrap': mock.Mock(return_value=pyramid_request)}
