# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.presenters.group_json import GroupJSONPresenter, GroupsJSONPresenter
from h.services.group_links import GroupLinksService
from h.resources import GroupResource


class TestGroupJSONPresenter(object):
    def test_private_group_asdict(self, factories, GroupResource_, links_svc):  # noqa: N803
        group = factories.Group(name='My Group',
                                pubid='mygroup')
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': 'mygroup',
            'organization': '',
            'type': 'private',
            'public': False,
            'scoped': False,
            'urls': links_svc.get_all.return_value,
            'links': links_svc.get_all.return_value,
        }

    def test_open_group_asdict(self, factories, GroupResource_, links_svc):  # noqa: N803
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': 'mygroup',
            'organization': '',
            'type': 'open',
            'public': True,
            'scoped': False,
            'urls': links_svc.get_all.return_value,
            'links': links_svc.get_all.return_value,
        }

    def test_open_scoped_group_asdict(self, factories, GroupResource_, links_svc):  # noqa: N803
        group = factories.OpenGroup(name='My Group',
                                    pubid='groupy',
                                    scopes=[factories.GroupScope(origin='http://foo.com')])
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': 'groupy',
            'type': 'open',
            'organization': '',
            'public': True,
            'scoped': True,
            'urls': links_svc.get_all.return_value,
            'links': links_svc.get_all.return_value,
        }

    def test_it_contains_deprecated_url_if_html_link_present(self, factories, GroupResource_, links_svc):  # noqa: N803
        links_svc.get_all.return_value = {
            'html': 'foobar'
        }
        group = factories.Group()
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        assert presenter.asdict()['url'] == 'foobar'

    def test_it_does_not_expand_by_default(self, factories, GroupResource_):  # noqa: N803
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        model = presenter.asdict()

        assert model['organization'] == ''

    def test_it_expands_organizations(self, factories, GroupResource_):  # noqa: N803
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        model = presenter.asdict(expand=['organization'])

        assert model['organization'] == {}  # empty organization

    def test_it_populates_expanded_organizations(self, factories, GroupResource_):  # noqa: N803
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group.organization = factories.Organization()
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        model = presenter.asdict(expand=['organization'])

        assert model['organization'] == {
            'name': group.organization.name,
            'id': group.organization.pubid,
        }

    def test_it_ignores_unrecognized_expands(self, factories, GroupResource_):  # noqa: N803
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        model = presenter.asdict(expand=['foobars', 'dingdong'])

        assert model['organization'] == ''


class TestGroupsJSONPresenter(object):

    def test_proxies_to_GroupJSONPresenter(self, factories, GroupJSONPresenter_, GroupResources):  # noqa: [N802, N803]
        groups = [factories.Group(), factories.OpenGroup()]
        group_resources = GroupResources(groups)
        presenter = GroupsJSONPresenter(group_resources)
        expected_call_args = [mock.call(group_resource) for group_resource in group_resources]

        presenter.asdicts()

        assert GroupJSONPresenter_.call_args_list == expected_call_args

    def test_asdicts_returns_list_of_dicts(self, factories, GroupResources):  # noqa: N803
        groups = [factories.Group(name=u'filbert'), factories.OpenGroup(name=u'delbert')]
        group_resources = GroupResources(groups)
        presenter = GroupsJSONPresenter(group_resources)

        result = presenter.asdicts()

        assert [group['name'] for group in result] == [u'filbert', u'delbert']

    def test_asdicts_injects_urls(self, factories, links_svc, GroupResources):  # noqa: N803
        groups = [factories.Group(), factories.OpenGroup()]
        group_resources = GroupResources(groups)
        presenter = GroupsJSONPresenter(group_resources)

        result = presenter.asdicts()

        for group_model in result:
            assert 'urls' in group_model
            assert 'links' in group_model


@pytest.fixture
def links_svc():
    return mock.create_autospec(GroupLinksService, spec_set=True, instance=True)


@pytest.fixture
def GroupResource_(links_svc):  # noqa: N802
    def resource_factory(group):
        return GroupResource(group, links_svc)
    return resource_factory


@pytest.fixture
def GroupResources(links_svc):  # noqa: N802
    def resource_factory(groups):
        return [GroupResource(group, links_svc) for group in groups]
    return resource_factory


@pytest.fixture
def GroupJSONPresenter_(patch):  # noqa: N802
    return patch('h.presenters.group_json.GroupJSONPresenter')
