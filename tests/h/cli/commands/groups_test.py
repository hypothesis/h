# -*- coding: utf-8 -*-

import mock
import pytest

from h.cli.commands import groups as groups_cli
from h.services.group import GroupService


class TestAddCommand(object):

    def test_it_creates_a_third_party_open_group(self, cli, cliconfig, group_service):
        result = cli.invoke(groups_cli.add_open_group,
                            [u'--name', 'Publisher', u'--authority', 'publisher.org',
                             u'--creator', 'admin', u'--origin', 'http://publisher.org'],
                            obj=cliconfig)

        assert result.exit_code == 0

        group_service.create_open_group.assert_called_once_with(
            name=u'Publisher',
            userid='acct:admin@publisher.org',
            origins=('http://publisher.org',),
        )

    def test_it_accepts_multiple_origin_options_on_the_command_line(self,
                                                                      cli,
                                                                      cliconfig,
                                                                      group_service):
        cli_options = [
            u'--name', 'Publisher',
            u'--authority', 'publisher.org',
            u'--creator', 'admin',
            u'--origin', 'https://hostname1.org',
            u'--origin', 'https://hostname2.org',
            u'--origin', 'https://hostname3.org:8080',
        ]

        result = cli.invoke(groups_cli.add_open_group, cli_options, obj=cliconfig)

        assert result.exit_code == 0
        assert group_service.create_open_group.call_args[1]['origins'] == (
            'https://hostname1.org', 'https://hostname2.org', 'https://hostname3.org:8080',
        )


@pytest.fixture
def group_service():
    return mock.create_autospec(GroupService, spec_set=True, instance=True)


@pytest.fixture
def cliconfig(pyramid_config, pyramid_request, group_service):
    pyramid_config.register_service(group_service, name='group')
    pyramid_request.tm = mock.Mock()
    return {'bootstrap': mock.Mock(return_value=pyramid_request)}
