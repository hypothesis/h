# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.presenters.group_json import GroupJSONPresenter, GroupsJSONPresenter


class TestGroupJSONPresenter(object):
    def test_private_group_asdict_no_urls(self, factories):
        group = factories.Group(name='My Group',
                                pubid='mygroup')

        presenter = GroupJSONPresenter(group)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': 'mygroup',
            'type': 'private',
            'public': False,
            'scoped': False,
            'urls': {}
        }

    def test_open_group_asdict_no_urls(self, factories):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')

        presenter = GroupJSONPresenter(group)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': 'mygroup',
            'type': 'open',
            'public': True,
            'scoped': False,
            'urls': {}
        }

    def test_private_group_asdict_with_urls(self, factories):
        group = factories.Group(name='My Group',
                                pubid='mygroup')
        route_url = mock.Mock(return_value='/group/a')
        presenter = GroupJSONPresenter(group, route_url=route_url)

        model = presenter.asdict()

        assert model['urls']['group'] == '/group/a'
        assert model['url'] == '/group/a'

    def test_open_group_asdict_with_urls(self, factories):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        route_url = mock.Mock(return_value='/group/a')
        presenter = GroupJSONPresenter(group, route_url=route_url)

        model = presenter.asdict()

        assert model['urls']['group'] == '/group/a'
        assert model['url'] == '/group/a'


class TestGroupsJSONPresenter(object):

    def test_proxies_to_GroupJSONPresenter(self, factories, GroupJSONPresenter_):  # noqa: [N802, N803]
        groups = [factories.Group(), factories.OpenGroup()]
        route_url = mock.Mock()
        presenter = GroupsJSONPresenter(groups, route_url=route_url)
        expected_call_args = [mock.call(group, route_url) for group in groups]

        presenter.asdicts()

        assert GroupJSONPresenter_.call_args_list == expected_call_args

    def test_asdicts_returns_list_of_dicts(self, factories):
        groups = [factories.Group(name=u'filbert'), factories.OpenGroup(name=u'delbert')]
        presenter = GroupsJSONPresenter(groups)

        result = presenter.asdicts()

        assert [group['name'] for group in result] == [u'filbert', u'delbert']

    def test_asdicts_injects_urls(self, factories):
        route_url = mock.Mock(return_value='/group/a')
        groups = [factories.Group(), factories.OpenGroup()]
        presenter = GroupsJSONPresenter(groups, route_url)

        result = presenter.asdicts()

        for group in result:
            assert group['url']
            assert group['urls']['group']


@pytest.fixture
def GroupJSONPresenter_(patch):  # noqa: N802
    return patch('h.presenters.group_json.GroupJSONPresenter')
