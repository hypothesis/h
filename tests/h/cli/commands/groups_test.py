# -*- coding: utf-8 -*-

import mock
import pytest

from h.cli.commands import groups as groups_cli
from h.services.group import GroupService


class TestAddCommand(object):

    def test_it_creates_a_third_party_open_group(self, cli, cliconfig, group_service):
        result = cli.invoke(groups_cli.add_open_group,
                            [u'--name', 'Publisher', u'--authority', 'publisher.org',
                             u'--creator', 'admin'],
                            obj=cliconfig)

        assert result.exit_code == 0

        group_service.create_open_group.assert_called_once_with(
            name=u'Publisher', userid='acct:admin@publisher.org')


@pytest.fixture
def group_service():
    return mock.create_autospec(GroupService, spec_set=True, instance=True)


@pytest.fixture
def cliconfig(pyramid_config, pyramid_request, group_service):
    pyramid_config.register_service(group_service, name='group')
    pyramid_request.tm = mock.Mock()
    return {'bootstrap': mock.Mock(return_value=pyramid_request)}
