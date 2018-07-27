# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services.list_groups import ListGroupsService
from h.services.list_groups import list_groups_factory


class TestListGroupsAllGroups(object):

    def test_returns_world_group_if_no_user(self, svc):
        results = svc.all_groups()

        assert '__world__' in [group.pubid for group in results]

    def test_returns_scoped_open_groups_if_no_user(self, svc, authority, scoped_open_groups):
        results = svc.all_groups(authority=authority)

        assert results == scoped_open_groups

    def test_returns_unscoped_open_groups_if_no_user(self, svc, authority, unscoped_open_groups):
        results = svc.all_groups(authority=authority)

        assert results == unscoped_open_groups

    def test_returns_all_open_groups_if_no_user(self, svc, authority, scoped_open_groups, unscoped_open_groups):
        results = svc.all_groups(authority=authority)

        for s_group in scoped_open_groups:
            assert s_group in results
        for u_group in unscoped_open_groups:
            assert u_group in results

    def test_returns_only_open_groups_if_no_user(self, svc, authority, scoped_open_groups, unscoped_open_groups):
        results = svc.all_groups(authority=authority)

        for group in results:
            assert group.type == 'open'

    def test_returns_world_group_if_user(self, svc, default_user):
        results = svc.all_groups(user=default_user)

        assert '__world__' in [group.pubid for group in results]

    def test_returns_scoped_open_groups_if_user(self, svc, user, scoped_open_groups):
        results = svc.all_groups(user=user)

        assert results == scoped_open_groups

    def test_returns_unscoped_open_groups_if_user(self, svc, user, unscoped_open_groups):
        results = svc.all_groups(user=user)

        assert results == unscoped_open_groups

    def test_returns_all_open_groups_if_user(self, svc, user, scoped_open_groups, unscoped_open_groups):
        expected_ids = {group.id for group in (scoped_open_groups + unscoped_open_groups)}

        results = svc.all_groups(user=user)
        actual_ids = {group.id for group in results}

        assert actual_ids == expected_ids

    def test_returns_private_groups_if_user(self, svc, user, private_groups):
        user.groups = private_groups

        results = svc.all_groups(user=user)

        assert results == private_groups

    def test_returns_open_and_private_groups_if_user(self, svc, user, scoped_open_groups, unscoped_open_groups, private_groups):
        user.groups = private_groups
        expected_ids = {group.id for group in (scoped_open_groups + unscoped_open_groups + private_groups)}

        results = svc.all_groups(user=user)
        actual_ids = {group.id for group in results}

        assert actual_ids == expected_ids

    def test_returns_groups_matching_authority_if_no_user(self, svc, alternate_authority, alternate_unscoped_open_groups, unscoped_open_groups):
        results = svc.all_groups(authority=alternate_authority)

        assert results == alternate_unscoped_open_groups

    def test_returns_groups_for_user_authority(self, svc, user, unscoped_open_groups):
        expected_ids = {group.id for group in unscoped_open_groups}

        results = svc.all_groups(user=user)

        actual_ids = {group.id for group in results}
        assert actual_ids == expected_ids

    def test_overrides_authority_param_if_user(self, svc, user, alternate_authority, alternate_unscoped_open_groups, unscoped_open_groups):
        # User has a different authority than authority param
        expected_ids = {group.id for group in unscoped_open_groups}

        results = svc.all_groups(user=user, authority=alternate_authority)

        actual_ids = {group.id for group in results}
        assert actual_ids == expected_ids

    def test_sorts_groups_by_type(self, svc, user, mixed_groups):
        expected_sorted_types = ['open', 'restricted', 'open', 'open', 'private', 'private']
        results = svc.all_groups(user=user)

        assert [group.type for group in results] == expected_sorted_types

    def test_sorts_groups_alphabetically(self, svc, user, mixed_groups):
        expected_sorted_pubids = ['wadsworth', 'xander', 'yaks', 'zebra', 'spectacle', 'yams']
        results = svc.all_groups(user=user)

        assert [group.pubid for group in results] == expected_sorted_pubids

    def test_returns_associated_groups_if_user(self,
                                               svc,
                                               authority,
                                               user,
                                               unscoped_restricted_groups,
                                               scoped_restricted_groups,
                                               scoped_open_groups,
                                               unscoped_open_groups,
                                               private_groups):
        user.groups = private_groups

        all_groups = scoped_open_groups + unscoped_open_groups + \
                     scoped_restricted_groups + unscoped_restricted_groups + \
                     private_groups
        expected = [group for group in all_groups if group.creator == user or user in group.members]
        results = svc.associated_groups(user=user)

        assert set(results) == set(expected)

    def test_returns_no_associated_groups_if_no_user(self, svc, authority):
        expected_ids = set({})

        results = svc.associated_groups()
        actual_ids = {group.id for group in results}

        assert actual_ids == expected_ids


class TestListGroupsSessionGroups(object):

    def test_it_returns_no_scoped_open_groups_except_world(self, svc, user, default_authority, mixed_groups):
        results = svc.session_groups(user=user, authority=default_authority)

        non_world_groups = [group for group in results if group.pubid != '__world__']

        for group in non_world_groups:
            assert group.type != 'open'

    def test_it_returns_no_unscoped_open_groups(self, svc, user, authority, unscoped_open_groups):
        results = svc.session_groups(user=user, authority=authority)

        assert results == []

    def test_it_returns_scoped_restricted_groups_if_user_member(self, svc, user, scoped_restricted_user_groups, authority):
        user.groups = scoped_restricted_user_groups
        results = svc.session_groups(user=user, authority=authority)

        assert results == user.groups
        for group in results:
            assert group.type == 'restricted'

    def test_it_excludes_scoped_restricted_groups_if_user_not_member(self, svc, user, scoped_restricted_groups, authority):
        expected = [group for group in scoped_restricted_groups if user in group.members]
        results = svc.session_groups(user=user, authority=authority)

        assert results == expected

    def test_it_returns_the_world_group(self, svc, user, default_authority):
        results = svc.session_groups(user=user, authority=default_authority)

        assert results[0].pubid == '__world__'

    def test_it_returns_world_group_only_if_no_user(self,
                                                    svc,
                                                    default_authority,
                                                    unscoped_restricted_groups,
                                                    scoped_restricted_groups,
                                                    unscoped_open_groups,
                                                    scoped_open_groups):
        results = svc.session_groups(user=None, authority=default_authority)

        assert results[0].pubid == '__world__'
        assert len(results) == 1

    def test_it_returns_private_groups_for_user(self, user, svc, authority, private_groups):
        user.groups = private_groups
        results = svc.session_groups(user=user, authority=authority)

        for group in user.groups:
            assert group in results
            assert group.type == 'private'

    def test_world_group_is_first(self, user, svc, default_authority, private_groups):
        user.groups = private_groups
        results = svc.session_groups(user=user, authority=default_authority)

        world_group = results.pop(0)
        assert world_group.pubid == '__world__'
        for group in results:
            assert group.type == 'private'


class TestListGroupsRequestGroups(object):

    def test_it_returns_world_group(self, svc, default_authority):
        results = svc.request_groups(authority=default_authority)

        assert results[0].pubid == '__world__'

    def test_it_returns_matching_scoped_open_groups(self, svc, authority, document_uri, scoped_open_groups):
        results = svc.request_groups(authority=authority, document_uri=document_uri)

        assert results == scoped_open_groups

    def test_it_returns_matching_scoped_restricted_groups(self, svc, authority, document_uri, scoped_restricted_groups):
        results = svc.request_groups(authority=authority, document_uri=document_uri)

        assert results == scoped_restricted_groups

    def test_it_returns_no_scoped_groups_if_uri_missing(self, svc, authority, scoped_open_groups, scoped_restricted_groups):
        results = svc.request_groups(authority=authority)

        assert results == []

    def test_it_returns_no_unscoped_open_groups(self, svc, authority, scoped_open_groups, unscoped_open_groups):
        results = svc.request_groups(authority=authority)

        assert results == []

    def test_it_returns_no_unscoped_restricted_groups(self, svc, authority, unscoped_restricted_groups):
        results = svc.request_groups(authority=authority)

        assert results == []

    def test_it_returns_no_unscoped_restricted_user_groups(self, svc, authority, user, unscoped_restricted_groups):
        user.groups = unscoped_restricted_groups
        results = svc.request_groups(user=user, authority=authority)

        assert results == []

    def test_it_returns_private_groups_if_user(self, svc, user, authority, private_groups):
        user.groups = private_groups
        results = svc.request_groups(user=user, authority=authority)

        assert results == private_groups

    def test_it_returns_no_group_dupes(self, svc, user, authority, private_groups, document_uri, scoped_restricted_user_groups):
        user.groups = private_groups + scoped_restricted_user_groups
        results = svc.request_groups(user=user, authority=authority, document_uri=document_uri)

        assert results == scoped_restricted_user_groups + private_groups

    def test_returned_open_groups_must_match_authority(self, svc, alternate_authority, unscoped_open_groups, scoped_open_groups):
        results = svc.request_groups(authority=alternate_authority)

        assert results == []

    def test_returned_restricted_groups_must_match_authority(self, svc, alternate_authority, scoped_restricted_groups):
        results = svc.request_groups(authority=alternate_authority)

        assert results == []

    def test_groups_are_sorted_by_type(self, svc, user, mixed_groups, authority, document_uri):
        expected_sorted_types = ['open', 'restricted', 'open', 'private', 'private']
        results = svc.request_groups(user=user, authority=authority, document_uri=document_uri)

        assert [group.type for group in results] == expected_sorted_types

    def test_groups_are_sorted_alphabetically(self, svc, user, mixed_groups, authority, document_uri):
        expected_sorted_pubids = ['wadsworth', 'xander', 'yaks', 'spectacle', 'yams']
        results = svc.request_groups(user=user, authority=authority, document_uri=document_uri)

        assert [group.pubid for group in results] == expected_sorted_pubids


class TestListGroupsFactory(object):

    def test_list_groups_factory(self, pyramid_request):
        svc = list_groups_factory(None, pyramid_request)

        assert isinstance(svc, ListGroupsService)

    def test_uses_request_authority(self, pyramid_request):
        pyramid_request.authority = 'bar.com'

        svc = list_groups_factory(None, pyramid_request)

        assert svc.request_authority == 'bar.com'


@pytest.fixture
def authority():
    """Return a consistent, different authority for groups in these tests"""
    return 'surreptitious.com'


@pytest.fixture
def default_authority(pyramid_request):
    """
    Return the test env request's default authority, i.e. 'example.com'

    Return the default authority—this automatically has a `__world__` group
    """
    return pyramid_request.authority


@pytest.fixture
def alternate_authority():
    return 'bar.com'


@pytest.fixture
def default_user(factories, default_authority):
    return factories.User(authority=default_authority)


@pytest.fixture
def user(factories, authority):
    return factories.User(authority=authority)


@pytest.fixture
def alternate_user(factories, alternate_authority):
    return factories.User(authority=alternate_authority)


@pytest.fixture
def origin():
    return 'http://foo.com'


@pytest.fixture
def document_uri():
    return 'http://foo.com/bar/fun.html'


@pytest.fixture
def scoped_open_groups(factories, authority, origin, user):
    return [
        factories.OpenGroup(authority=authority,
                            creator=user,
                            scopes=[factories.GroupScope(origin=origin)]),
        factories.OpenGroup(authority=authority,
                            scopes=[factories.GroupScope(origin=origin)])
    ]


@pytest.fixture
def scoped_restricted_groups(factories, authority, origin, user):
    return [
        factories.RestrictedGroup(authority=authority,
                                  creator=user,
                                  scopes=[factories.GroupScope(origin=origin)]),
        factories.RestrictedGroup(authority=authority,
                                  scopes=[factories.GroupScope(origin=origin)])
    ]


@pytest.fixture
def unscoped_restricted_groups(factories, authority, user):
    return [
        factories.RestrictedGroup(authority=authority, creator=user),
        factories.RestrictedGroup(authority=authority)
    ]


@pytest.fixture
def scoped_restricted_user_groups(factories, authority, user, origin):
    return [
        factories.RestrictedGroup(name='Alpha',
                                  authority=authority,
                                  creator=user,
                                  scopes=[factories.GroupScope(origin=origin)]),
        factories.RestrictedGroup(
                                  name='Beta',
                                  authority=authority,
                                  creator=user,
                                  scopes=[factories.GroupScope(origin=origin)])
    ]


@pytest.fixture
def unscoped_open_groups(factories, authority, user):
    return [
        factories.OpenGroup(authority=authority, creator=user),
        factories.OpenGroup(authority=authority)
    ]


@pytest.fixture
def alternate_unscoped_open_groups(factories, alternate_authority):
    return [
        factories.OpenGroup(authority=alternate_authority),
        factories.OpenGroup(authority=alternate_authority)
    ]


@pytest.fixture
def private_groups(factories, authority):
    return [
        factories.Group(authority=authority),
        factories.Group(authority=authority)
    ]


@pytest.fixture
def mixed_groups(factories, user, authority, origin):
    """Return a list of open groups with different names and scope/not scoped"""
    user.groups = [
        factories.Group(name='Yams', pubid='yams', authority=authority),
        factories.Group(name='Spectacle', pubid='spectacle', authority=authority)
    ]
    return [
        factories.OpenGroup(name='Zebra',
                            pubid='zebra',
                            authority=authority),
        factories.OpenGroup(name='Yaks',
                            pubid='yaks',
                            authority=authority,
                            scopes=[factories.GroupScope(origin=origin)]),
        factories.RestrictedGroup(name='Xander',
                                  pubid='xander',
                                  authority=authority,
                                  scopes=[factories.GroupScope(origin=origin)]),
        factories.OpenGroup(name='wadsworth',
                            pubid='wadsworth',
                            authority=authority,
                            scopes=[factories.GroupScope(origin=origin)])
    ]


@pytest.fixture
def svc(pyramid_request, db_session):
    return ListGroupsService(
        session=db_session,
        request_authority=pyramid_request.authority
    )
