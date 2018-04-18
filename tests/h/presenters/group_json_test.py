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
            'organization': group_resource.organization.id,
            'type': 'private',
            'public': False,
            'scoped': False,
            'links': links_svc.get_all.return_value,
        }

    def test_open_group_asdict(self, factories, GroupResource_, links_svc):  # noqa: N803
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': group_resource.id,
            'organization': group_resource.organization.id,
            'type': 'open',
            'public': True,
            'scoped': False,
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
            'organization': group_resource.organization.id,
            'public': True,
            'scoped': True,
            'links': links_svc.get_all.return_value,
        }

    def test_it_does_not_contain_deprecated_url(self, factories, GroupResource_, links_svc):  # noqa: N803
        links_svc.get_all.return_value = {
            'html': 'foobar'
        }
        group = factories.Group()
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        assert 'url' not in presenter.asdict()

    def test_it_does_not_expand_by_default(self, factories, GroupResource_):  # noqa: N803
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        model = presenter.asdict()

        assert model['organization'] == group_resource.organization.id

    def test_it_expands_organizations(self, factories, GroupResource_, OrganizationJSONPresenter):  # noqa: N803
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        model = presenter.asdict(expand=['organization'])

        assert model['organization'] == OrganizationJSONPresenter(group_resource.organization).asdict.return_value

    def test_it_ignores_unrecognized_expands(self, factories, GroupResource_):  # noqa: N803
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_resource = GroupResource_(group)
        presenter = GroupJSONPresenter(group_resource)

        model = presenter.asdict(expand=['foobars', 'dingdong'])

        assert model['organization'] == group_resource.organization.id


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

    def test_asdicts_injects_links(self, factories, links_svc, GroupResources):  # noqa: N803
        groups = [factories.Group(), factories.OpenGroup()]
        group_resources = GroupResources(groups)
        presenter = GroupsJSONPresenter(group_resources)

        result = presenter.asdicts()

        for group_model in result:
            assert 'links' in group_model


@pytest.fixture
def links_svc(pyramid_config):
    svc = mock.create_autospec(GroupLinksService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name='group_links')
    return svc


@pytest.fixture
def GroupResource_(pyramid_request, links_svc):  # noqa: N802
    def resource_factory(group):
        return GroupResource(group, pyramid_request)
    return resource_factory


@pytest.fixture
def GroupResources(pyramid_request, links_svc):  # noqa: N802
    def resource_factory(groups):
        return [GroupResource(group, pyramid_request) for group in groups]
    return resource_factory


@pytest.fixture
def GroupJSONPresenter_(patch):  # noqa: N802
    return patch('h.presenters.group_json.GroupJSONPresenter')


@pytest.fixture
def OrganizationJSONPresenter(patch):  # noqa: N802
    return patch('h.presenters.group_json.OrganizationJSONPresenter')
