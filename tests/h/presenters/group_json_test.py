# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.presenters.group_json import GroupJSONPresenter, GroupsJSONPresenter
from h.services.group_links import GroupLinksService
from h import traversal


class TestGroupJSONPresenter(object):
    def test_private_group_asdict(self, factories, GroupContext, links_svc):
        group = factories.Group(name='My Group',
                                pubid='mygroup')
        group_context = GroupContext(group)
        presenter = GroupJSONPresenter(group_context)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': 'mygroup',
            'organization': group_context.organization.id,
            'type': 'private',
            'public': False,
            'scoped': False,
            'links': links_svc.get_all.return_value,
        }

    def test_open_group_asdict(self, factories, GroupContext, links_svc):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_context = GroupContext(group)
        presenter = GroupJSONPresenter(group_context)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': group_context.id,
            'organization': group_context.organization.id,
            'type': 'open',
            'public': True,
            'scoped': False,
            'links': links_svc.get_all.return_value,
        }

    def test_open_scoped_group_asdict(self, factories, GroupContext, links_svc):
        group = factories.OpenGroup(name='My Group',
                                    pubid='groupy',
                                    scopes=[factories.GroupScope(origin='http://foo.com')])
        group_context = GroupContext(group)
        presenter = GroupJSONPresenter(group_context)

        assert presenter.asdict() == {
            'name': 'My Group',
            'id': 'groupy',
            'type': 'open',
            'organization': group_context.organization.id,
            'public': True,
            'scoped': True,
            'links': links_svc.get_all.return_value,
        }

    def test_it_does_not_contain_deprecated_url(self, factories, GroupContext, links_svc):
        links_svc.get_all.return_value = {
            'html': 'foobar'
        }
        group = factories.Group()
        group_context = GroupContext(group)
        presenter = GroupJSONPresenter(group_context)

        assert 'url' not in presenter.asdict()

    def test_it_sets_organization_None_if_group_has_no_organization(self, factories, GroupContext):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group.organization = None
        group_context = GroupContext(group)
        presenter = GroupJSONPresenter(group_context)

        model = presenter.asdict()

        assert model['organization'] is None

    def test_it_does_not_expand_by_default(self, factories, GroupContext):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_context = GroupContext(group)
        presenter = GroupJSONPresenter(group_context)

        model = presenter.asdict()

        assert model['organization'] == group_context.organization.id

    def test_it_expands_organizations(self, factories, GroupContext, OrganizationJSONPresenter):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_context = GroupContext(group)
        presenter = GroupJSONPresenter(group_context)

        model = presenter.asdict(expand=['organization'])

        assert model['organization'] == OrganizationJSONPresenter(group_context.organization).asdict.return_value

    def test_expanded_organizations_None_if_missing(self, factories, GroupContext, OrganizationJSONPresenter):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group.organization = None
        group_context = GroupContext(group)
        presenter = GroupJSONPresenter(group_context)

        model = presenter.asdict(expand=['organization'])

        assert model['organization'] is None

    def test_it_ignores_unrecognized_expands(self, factories, GroupContext):
        group = factories.OpenGroup(name='My Group',
                                    pubid='mygroup')
        group_context = GroupContext(group)
        presenter = GroupJSONPresenter(group_context)

        model = presenter.asdict(expand=['foobars', 'dingdong'])

        assert model['organization'] == group_context.organization.id


class TestGroupsJSONPresenter(object):

    def test_proxies_to_GroupJSONPresenter(self, factories, GroupJSONPresenter_, GroupContexts):
        groups = [factories.Group(), factories.OpenGroup()]
        group_contexts = GroupContexts(groups)
        presenter = GroupsJSONPresenter(group_contexts)
        expected_call_args = [mock.call(group_context) for group_context in group_contexts]

        presenter.asdicts()

        assert GroupJSONPresenter_.call_args_list == expected_call_args

    def test_asdicts_returns_list_of_dicts(self, factories, GroupContexts):
        groups = [factories.Group(name='filbert'), factories.OpenGroup(name='delbert')]
        group_contexts = GroupContexts(groups)
        presenter = GroupsJSONPresenter(group_contexts)

        result = presenter.asdicts()

        assert [group['name'] for group in result] == ['filbert', 'delbert']

    def test_asdicts_injects_links(self, factories, links_svc, GroupContexts):
        groups = [factories.Group(), factories.OpenGroup()]
        group_contexts = GroupContexts(groups)
        presenter = GroupsJSONPresenter(group_contexts)

        result = presenter.asdicts()

        for group_model in result:
            assert 'links' in group_model


@pytest.fixture
def links_svc(pyramid_config):
    svc = mock.create_autospec(GroupLinksService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name='group_links')
    return svc


@pytest.fixture
def GroupContext(pyramid_request, links_svc):
    def resource_factory(group):
        return traversal.GroupContext(group, pyramid_request)
    return resource_factory


@pytest.fixture
def GroupContexts(pyramid_request, links_svc):
    def resource_factory(groups):
        return [traversal.GroupContext(group, pyramid_request) for group in groups]
    return resource_factory


@pytest.fixture
def GroupJSONPresenter_(patch):
    return patch('h.presenters.group_json.GroupJSONPresenter')


@pytest.fixture
def OrganizationJSONPresenter(patch):
    return patch('h.presenters.group_json.OrganizationJSONPresenter')
