# -*- coding: utf-8 -*-

import mock
import pytest

from h.cli.commands import groups as groups_cli


class TestAddCommand(object):

    def test_it_creates_a_publisher_group(self, cli, cliconfig, group_service):
        """this is deprecated and now called 'open', but keeping this to not break scripts"""
        name = 'Publisher Group Name'
        creator = 'admin'
        authority = 'publisher.org'
        result = cli.invoke(groups_cli.add_publisher_group,
                            [u'--name', name,
                             u'--authority', authority,
                             u'--creator', creator],
                            obj=cliconfig)

        assert result.exit_code == 0

        group_service.create.assert_called_with(authority=authority,
                                                name=name,
                                                userid='acct:{0}@{1}'.format(
                                                    creator, authority),
                                                type_='open')

    def test_it_creates_a_public_group(self, cli, cliconfig, group_service):
        name = 'Public Group Name'
        creator = 'admin'
        authority = 'publisher.org'
        result = cli.invoke(groups_cli.add_public_group,
                            [u'--name', name,
                             u'--authority', authority,
                             u'--creator', creator],
                            obj=cliconfig)

        assert result.exit_code == 0

        group_service.create.assert_called_with(authority=authority,
                                                name=name,
                                                userid='acct:{0}@{1}'.format(
                                                    creator, authority),
                                                type_='public')

    def test_it_creates_a_open_group(self, cli, cliconfig, group_service):
        name = 'Open Group Name'
        creator = 'admin'
        authority = 'publisher.org'
        result = cli.invoke(groups_cli.add_open_group,
                            [u'--name', name,
                             u'--authority', authority,
                             u'--creator', creator],
                            obj=cliconfig)

        assert result.exit_code == 0

        group_service.create.assert_called_with(authority=authority,
                                                name=name,
                                                userid='acct:{0}@{1}'.format(
                                                    creator, authority),
                                                type_='open')


@pytest.fixture
def group_service(pyramid_config):
    group_service = mock.Mock(spec_set=['create', 'member_join'])
    return group_service


@pytest.fixture
def cliconfig(pyramid_config, pyramid_request, group_service):
    pyramid_config.register_service(group_service, name='group')
    pyramid_request.tm = mock.Mock()
    return {'bootstrap': mock.Mock(return_value=pyramid_request)}


class TestJoinCommand(object):
    """test cli group join --name username --authority localhost --group pubid"""

    def test_it_adds_user_to_group(self, db_session, cli, cliconfig, group_service, factories):
        authority = u'publisher.org'
        username_of_user_to_add = u'ben'
        user_to_add = factories.User(
            username=username_of_user_to_add, authority=authority)
        pubid = u'pubid'
        group = factories.Group(pubid=pubid, authority=authority)
        db_session.commit()

        result = cli.invoke(groups_cli.join,
                            [u'--user', user_to_add.username,
                             u'--authority', authority,
                             u'--group', group.pubid],
                            obj=cliconfig)

        assert result.exit_code == 0

        group_service.member_join.assert_called_once()
        first_call_args = group_service.member_join.call_args[0]
        assert first_call_args[0].pubid == 'pubid'

    def test_error_when_user_doesnt_exist(self, db_session, cli, cliconfig, group_service, factories):
        authority = u'publisher.org'
        username_of_user_to_add = u'ben'
        pubid = u'pubid'
        group = factories.Group(pubid=pubid, authority=authority)
        db_session.commit()

        result = cli.invoke(groups_cli.join,
                            [u'--user', username_of_user_to_add,
                             u'--authority', authority,
                             u'--group', group.pubid],
                            obj=cliconfig)

        assert result.exit_code == -1
        assert username_of_user_to_add in result.exception.message

    def test_error_when_group_doesnt_exist(self, db_session, cli, cliconfig, group_service, factories):
        authority = u'publisher.org'
        username_of_user_to_add = u'ben'
        user_to_add = factories.User(
            username=username_of_user_to_add, authority=authority)
        pubid = u'pubid'
        db_session.commit()

        result = cli.invoke(groups_cli.join,
                            [u'--user', user_to_add.username,
                             u'--authority', authority,
                             u'--group', pubid],
                            obj=cliconfig)

        assert result.exit_code == -1
        assert pubid in result.exception.message
