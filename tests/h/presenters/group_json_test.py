# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.presenters.group_json import GroupJSONPresenter, GroupsJSONPresenter
from h.services.group_links import GroupLinksService


class TestGroupJSONPresenter(object):
    def test_private_group_asdict_no_links_svc(self, factories):
        group = factories.Group(name='My Group',
                                pubid='mygroup')

        presenter = GroupJSONPresenter(group)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': 'mygroup',
            'organization': '',
            'type': 'private',
            'public': False,
            'scoped': False,
            'urls': {},
            'links': {}
        }

    def test_open_group_asdict_no_links_svc(self, factories):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')

        presenter = GroupJSONPresenter(group)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': 'mygroup',
            'organization': '',
            'type': 'open',
            'public': True,
            'scoped': False,
            'urls': {},
            'links': {}
        }

    def test_open_scoped_group_asdict(self, factories):
        group = factories.OpenGroup(name='My Group',
                                    pubid='groupy',
                                    scopes=[factories.GroupScope(origin='http://foo.com')])

        presenter = GroupJSONPresenter(group)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': 'groupy',
            'type': 'open',
            'organization': '',
            'public': True,
            'scoped': True,
            'urls': {},
            'links': {},
        }

    def test_private_group_asdict_with_links_svc(self, factories, links_svc):
        group = factories.Group(name='My Group',
                                pubid='mygroup')
        presenter = GroupJSONPresenter(group, links_svc=links_svc)
        links_svc.get_all.return_value = {'html': 'bar'}

        model = presenter.asdict()

        links_svc.get_all.assert_called_once_with(group)
        assert model['urls'] == links_svc.get_all.return_value
        assert model['links'] == links_svc.get_all.return_value
        assert model['url'] == links_svc.get_all.return_value['html']

    def test_open_group_asdict_with_links_svc(self, factories, links_svc):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        presenter = GroupJSONPresenter(group, links_svc=links_svc)

        presenter.asdict()

        links_svc.get_all.assert_called_once_with(group)

    def test_it_does_not_expand_by_default(self, factories):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        presenter = GroupJSONPresenter(group)

        model = presenter.asdict()

        assert model['organization'] == ''

    def test_it_expands_organizations(self, factories):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        presenter = GroupJSONPresenter(group)

        model = presenter.asdict(expand=['organization'])

        assert model['organization'] == {}  # empty organization

    def test_it_populates_expanded_organizations(self, factories):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group.organization = factories.Organization()
        presenter = GroupJSONPresenter(group)

        model = presenter.asdict(expand=['organization'])

        assert model['organization'] == {
            'name': group.organization.name,
            'id': group.organization.pubid,
        }

    def test_it_ignores_unrecognized_expands(self, factories):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        presenter = GroupJSONPresenter(group)

        model = presenter.asdict(expand=['foobars', 'dingdong'])

        assert model['organization'] == ''


class TestGroupsJSONPresenter(object):

    def test_proxies_to_GroupJSONPresenter(self, factories, GroupJSONPresenter_, links_svc):  # noqa: [N802, N803]
        groups = [factories.Group(), factories.OpenGroup()]
        presenter = GroupsJSONPresenter(groups, links_svc=links_svc)
        expected_call_args = [mock.call(group, links_svc) for group in groups]

        presenter.asdicts()

        assert GroupJSONPresenter_.call_args_list == expected_call_args

    def test_asdicts_returns_list_of_dicts(self, factories):
        groups = [factories.Group(name=u'filbert'), factories.OpenGroup(name=u'delbert')]
        presenter = GroupsJSONPresenter(groups)

        result = presenter.asdicts()

        assert [group['name'] for group in result] == [u'filbert', u'delbert']

    def test_asdicts_injects_urls(self, factories, links_svc):
        groups = [factories.Group(), factories.OpenGroup()]
        presenter = GroupsJSONPresenter(groups, links_svc)

        result = presenter.asdicts()

        for group_model in result:
            assert 'urls' in group_model
            assert 'links' in group_model


@pytest.fixture
def links_svc():
    return mock.create_autospec(GroupLinksService, spec_set=True, instance=True)


@pytest.fixture
def GroupJSONPresenter_(patch):  # noqa: N802
    return patch('h.presenters.group_json.GroupJSONPresenter')
