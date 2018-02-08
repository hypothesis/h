# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.services.list_groups import ListGroupsService
from h.services.list_groups import list_groups_factory


class TestListGroupsAllGroups(object):

    def test_returns_open_groups_when_no_user(self, list_groups_service, open_groups):
        open_group_ids = {group.pubid for group in open_groups}
        open_group_ids.add('__world__')

        groups = list_groups_service.all_groups()

        assert {group['id'] for group in groups} == open_group_ids
        for group in groups:
            assert group['type'] == 'open'

    def test_returns_all_group_types_when_user(self, list_groups_service, factories):
        user = factories.User()
        user.groups = [factories.Group(), factories.Group()]
        expected_ids = [group.pubid for group in user.groups]
        expected_ids.append('__world__')

        groups = list_groups_service.all_groups(user=user)

        group_ids = [group['id'] for group in groups]
        for expected_id in expected_ids:
            assert expected_id in group_ids

    def test_ignores_authority_when_user_present(self, list_groups_service, factories, authority_open_groups):
        user = factories.User(authority='foo.com')
        another_authority_open_group = factories.OpenGroup(authority='somewhere-else.com')
        auth_group_ids = {group.pubid for group in authority_open_groups}

        groups = list_groups_service.all_groups(user=user, authority='somewhere-else.com')

        group_ids = {group['id'] for group in groups}
        assert group_ids == auth_group_ids
        assert another_authority_open_group.pubid not in group_ids

    def test_groups_are_sorted(self, list_groups_service, factories):
        user = factories.User(authority='z.com')
        user.groups = [factories.Group(name='alpha', pubid='zzzz', authority='z.com'),
                       factories.Group(name='alpha', pubid='aaaa', authority='z.com'),
                       factories.Group(name='aardvark', pubid='zoinks', authority='z.com')]
        factories.OpenGroup(name='alpha', pubid='zaza', authority='z.com')
        factories.OpenGroup(name='alpha', pubid='azaz', authority='z.com')

        groups = list_groups_service.all_groups(user=user)

        # open groups first
        assert [group['id'] for group in groups] == ['azaz', 'zaza', 'zoinks', 'aaaa', 'zzzz']

    def test_groups_are_sorted_alphabetically(self, list_groups_service, factories):
        user = factories.User(authority='z.com')
        user.groups = [factories.Group(name='Lilac', authority='z.com'),
                       factories.Group(name='foobar', authority='z.com')]

        groups = list_groups_service.all_groups(user=user)

        assert [group.name for group in groups] == ['foobar', 'Lilac']

    def test_user_groups_not_mutated(self, list_groups_service, factories):
        user = factories.User(authority='z.com')
        user.groups = [factories.Group(name='Lilac', authority='z.com'),
                       factories.Group(name='Alpha', authority='z.com'),
                       factories.Group(name='foobar', authority='z.com')]

        list_groups_service.all_groups(user=user)

        assert [group.name for group in user.groups] == ['Lilac', 'Alpha', 'foobar']

    @pytest.fixture
    def open_groups(self, factories):
        return [factories.OpenGroup(), factories.OpenGroup()]


class TestListGroupsPrivateGroups(object):

    @pytest.mark.parametrize('attribute', [
        ('id'),
        ('name'),
        ('public'),
        ('scoped'),
        ('type')
    ])
    def test_returns_formatted_groups(self, list_groups_service, factories, attribute):
        user = factories.User()
        user.groups = [factories.Group()]

        groups = list_groups_service.private_groups(user)

        assert attribute in groups[0]

    def test_returns_private_groups_only(self, list_groups_service, factories):
        user = factories.User()
        user.groups = [factories.Group(), factories.Group(), factories.Group()]

        groups = list_groups_service.private_groups(user)

        assert len(groups) == 3
        for group in groups:
            assert group['type'] == 'private'

    def test_returns_empty_when_user_no_private_groups(self, list_groups_service, factories):
        user = factories.User()

        groups = list_groups_service.private_groups(user)

        assert groups == []

    def test_returns_no_groups_for_no_user(self, list_groups_service):

        groups = list_groups_service.private_groups(user=None)

        assert groups == []

    def test_groups_are_sorted(self, list_groups_service, factories):
        user = factories.User(authority='z.com')
        user.groups = [factories.Group(name='alpha', pubid='zzzz', authority='z.com'),
                       factories.Group(name='alpha', pubid='aaaa', authority='z.com'),
                       factories.Group(name='aardvark', pubid='zoinks', authority='z.com')]

        groups = list_groups_service.private_groups(user=user)

        assert [group['id'] for group in groups] == ['zoinks', 'aaaa', 'zzzz']


class TestListGroupsOpenGroups(object):

    def test_returns_authority_open_groups(self, list_groups_service, authority_open_groups):
        o_group_names = {o_group.name for o_group in authority_open_groups}

        groups = list_groups_service.open_groups(authority='foo.com')

        assert {group['name'] for group in groups} == o_group_names

    def test_no_groups_from_mismatched_authority(self, list_groups_service, authority_open_groups):

        groups = list_groups_service.open_groups(authority='bar.com')

        assert groups == []

    def test_returns_groups_from_default_authority(self, list_groups_service):
        groups = list_groups_service.open_groups()

        assert groups[0]['id'] == '__world__'

    def test_returns_groups_for_user_authority(self, list_groups_service, authority_open_groups, factories):
        user = factories.User(authority='foo.com')
        o_group_names = {o_group.name for o_group in authority_open_groups}

        o_groups = list_groups_service.open_groups(user=user)

        assert {group['name'] for group in o_groups} == o_group_names

    def test_ignores_authority_if_user(self, list_groups_service, authority_open_groups, factories):
        user = factories.User(authority='somethingelse.com')

        o_groups = list_groups_service.open_groups(user=user, authority='foo.com')

        assert o_groups == []

    def test_groups_are_sorted(self, list_groups_service, factories):
        factories.OpenGroup(name='alpha', pubid='zzzz', authority='z.com')
        factories.OpenGroup(name='alpha', pubid='aaaa', authority='z.com')
        factories.OpenGroup(name='aardvark', pubid='zoinks', authority='z.com')

        groups = list_groups_service.open_groups(authority='z.com')

        assert [group['id'] for group in groups] == ['zoinks', 'aaaa', 'zzzz']


class TestListGroupsFactory(object):

    def test_list_groups_factory(self, pyramid_request):
        svc = list_groups_factory(None, pyramid_request)

        assert isinstance(svc, ListGroupsService)

    def test_uses_request_authority(self, pyramid_request):
        pyramid_request.authority = 'bar.com'

        svc = list_groups_factory(None, pyramid_request)

        assert svc.request_authority == 'bar.com'


@pytest.fixture
def authority_open_groups(factories):
    return [factories.OpenGroup(authority='foo.com'),
            factories.OpenGroup(authority='foo.com')]


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.route_url = mock.Mock(return_value='/group/a')
    return pyramid_request


@pytest.fixture
def list_groups_service(pyramid_request, db_session):
    return ListGroupsService(
        session=db_session,
        request_authority=pyramid_request.authority,
        route_url=pyramid_request.route_url
    )
