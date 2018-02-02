# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.models.group import ReadableBy, WriteableBy
from h.services.profile_group import ProfileGroupService
from h.services.profile_group import profile_groups_factory


class TestProfileGroupService(object):
    def test_all_returns_private_groups_for_user(self, profile_group_factory, user):
        svc = profile_group_factory([])

        groups = svc.all(user)

        assert ([group['id'] for group in groups] ==
                [group.pubid for group in user.groups])

    def test_all_returns_no_private_groups_for_no_user(self, profile_group_factory):
        svc = profile_group_factory([])

        groups = svc.all(user=None)

        assert groups == []

    def test_all_returns_world_group_for_no_user(self, profile_group_factory, world_group):
        svc = profile_group_factory([world_group])

        groups = svc.all(user=None)

        assert groups[0]['id'] == world_group.pubid

    def test_all_returns_open_groups_for_no_user(self, profile_group_factory, open_groups):
        svc = profile_group_factory(open_groups)

        groups = svc.all(user=None)

        assert [group['id'] for group in groups] == [group.pubid for group in open_groups]

    def test_sort_sorts_private_groups_by_name(self, profile_group_factory, factories):
        user = factories.User()
        user.groups = [factories.Group(name='zedd'),
                       factories.Group(name='alpha')]
        svc = profile_group_factory([])

        groups = svc.all(user)

        names = [group['name'] for group in groups]
        assert names == ['alpha', 'zedd']

    def test_sort_sorts_private_groups_by_pubid(self, profile_group_factory, factories):
        user = factories.User()
        user.groups = [factories.Group(name='zedd', pubid='yyyyy'),
                       factories.Group(name='alpha', pubid='zzzzz'),
                       factories.Group(name='zedd', pubid='aaaaa')]
        svc = profile_group_factory([])

        groups = svc.all(user)

        sorted_groups = [(group['id'], group['name']) for group in groups]
        assert sorted_groups == [('zzzzz', 'alpha'), ('aaaaa', 'zedd'), ('yyyyy', 'zedd')]

    def test_sort_sorts_public_groups_by_name(self, profile_group_factory, factories):
        svc = profile_group_factory([
            factories.OpenGroup(name='zedd', pubid='aaaaa'),
            factories.OpenGroup(name='alpha', pubid='zzzzz')
        ])

        groups = svc.all()

        names = [group['name'] for group in groups]
        assert names == ['alpha', 'zedd']

    def test_sort_sorts_public_groups_by_pubid(self, profile_group_factory, factories):
        svc = profile_group_factory([
            factories.OpenGroup(name='zedd', pubid='yyyyy'),
            factories.OpenGroup(name='zedd', pubid='aaaaa'),
            factories.OpenGroup(name='alpha', pubid='zzzzz')
        ])

        groups = svc.all()

        sorted_groups = [(group['id'], group['name']) for group in groups]
        assert sorted_groups == [('zzzzz', 'alpha'), ('aaaaa', 'zedd'), ('yyyyy', 'zedd')]

    def test_sort_sorts_groups_by_type(self, profile_group_factory, factories):
        """ open groups should come first """
        user = factories.User()
        user.groups = [
            factories.Group(name='zebra2', pubid='apple'),
            factories.Group(name='zebra', pubid='zebra')
        ]
        svc = profile_group_factory([
            factories.OpenGroup(name='zedd', pubid='yyyyy'),
            factories.OpenGroup(name='alpha', pubid='zzzzz')
        ])

        groups = svc.all(user)

        names = [group['name'] for group in groups]
        assert names == ['alpha', 'zedd', 'zebra', 'zebra2']

    def test_all_proxies_authority_parameter_to_svc(self, db_session, pyramid_request):
        auth_group_svc = mock.Mock(spec_set=['public_groups'])
        auth_group_svc.public_groups.return_value = []
        svc = ProfileGroupService(
          db_session,
          request_authority=pyramid_request.authority,
          route_url=pyramid_request.route_url,
          open_group_finder=auth_group_svc.public_groups
        )

        svc.all(user=None, authority="foo")

        auth_group_svc.public_groups.assert_called_once_with("foo")

    @pytest.mark.parametrize('attribute', [
        ('id'),
        ('name'),
        ('public'),
        ('scoped'),
        ('type')
    ])
    def test_all_includes_group_attributes(self, profile_group_factory, open_groups, user, attribute):
        svc = profile_group_factory(open_groups)

        groups = svc.all(user)

        assert attribute in groups[0]

    def test_open_groups_do_not_have_group_url(self, profile_group_factory, open_groups):
        svc = profile_group_factory(open_groups)

        groups = svc.all()

        for open_group in groups:
            assert 'url' not in open_group
            assert 'group' not in open_group['urls']

    def test_private_groups_have_group_url(self, profile_group_factory, user):
        svc = profile_group_factory([])

        groups = svc.all(user)

        for private_group in groups:
            assert 'url' in private_group
            assert 'group' in private_group['urls']


@pytest.mark.usefixtures('authority_group_service')
class TestProfileGroupsFactory(object):
    def test_returns_profile_group_service(self, pyramid_request):
        svc = profile_groups_factory(None, pyramid_request)

        assert isinstance(svc, ProfileGroupService)

    def test_provides_request_db_as_session(self, pyramid_request):
        svc = profile_groups_factory(None, pyramid_request)

        assert svc.session == pyramid_request.db

    def test_wraps_auth_group_service_as_finder(self, pyramid_request, authority_group_service):
        svc = profile_groups_factory(None, pyramid_request)

        svc.all(authority='foo')

        authority_group_service.public_groups.assert_called_once_with('foo')


@pytest.mark.usefixtures('authority_group_service')
class TestProfileGroupsAuthority(object):
    def test_accepts_any_authority_for_unauthed_user(self, pyramid_request, authority_group_service):
        svc = profile_groups_factory(None, pyramid_request)

        svc.all(authority='foo')

        authority_group_service.public_groups.assert_called_once_with('foo')

    def test_overrides_authority_with_user_authority(self, pyramid_request, factories, authority_group_service):
        pyramid_request.authority = 'rando.com'
        svc = profile_groups_factory(None, pyramid_request)
        user = factories.User()

        svc.all(user)

        authority_group_service.public_groups.assert_called_once_with(user.authority)

    def test_authority_default_to_request_for_unauthenticated_user(self, pyramid_request, authority_group_service):
        pyramid_request.authority = 'rando.com'
        svc = profile_groups_factory(None, pyramid_request)

        svc.all()

        authority_group_service.public_groups.assert_called_once_with('rando.com')


class FakeAuthorityGroupService(object):

    def __init__(self, public_groups):
        self._public_groups = public_groups

    def public_groups(self, authority):
        return self._public_groups


@pytest.fixture
def user(factories):
    user = factories.User(username='freya')
    user.groups = [factories.Group(), factories.Group()]
    return user


@pytest.fixture
def world_group(factories):
    return factories.Group(name=u'Public',
                           joinable_by=None,
                           readable_by=ReadableBy.world,
                           writeable_by=WriteableBy.authority)


@pytest.fixture
def open_groups(factories):
    return [factories.OpenGroup(), factories.OpenGroup()]


@pytest.fixture
def authority_group_service(pyramid_config):
    service = mock.Mock(spec_set=['public_groups'])
    service.public_groups.return_value = None
    pyramid_config.register_service(service, name='authority_group')
    return service


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.route_url = mock.Mock(return_value='/group/a')
    return pyramid_request


@pytest.fixture
def profile_group_factory(db_session, pyramid_request, request_authority=None):
    """
    Return a callable that will create a ProfileGroupService.

    Return a callable that will create a ProfileGroupService
    with a fake AuthorityGroupService whose ``public_groups``
    will return the passed ``open_groups``
    """
    r_authority = request_authority or pyramid_request.authority

    def service_builder(open_groups):
        return ProfileGroupService(
          session=db_session,
          request_authority=r_authority,
          route_url=pyramid_request.route_url,
          open_group_finder=FakeAuthorityGroupService(open_groups).public_groups
         )
    return service_builder
