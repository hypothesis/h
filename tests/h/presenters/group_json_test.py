# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock

from h.presenters.group_json import GroupJSONPresenter


class TestUserJSONPresenter(object):
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
        print model

        assert model['urls']['group'] == '/group/a'
        assert model['url'] == '/group/a'

    def test_open_group_asdict_with_urls(self, factories):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        route_url = mock.Mock(return_value='/group/a')
        presenter = GroupJSONPresenter(group, route_url=route_url)

        model = presenter.asdict()
        print model

        assert model['urls']['group'] == '/group/a'
        assert model['url'] == '/group/a'
