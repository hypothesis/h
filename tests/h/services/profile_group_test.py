# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.models.group import JoinableBy, ReadableBy, WriteableBy
from h.services.profile_group import ProfileGroupService
from h.services.profile_group import profile_groups_factory

class TestProfileGroupService(object):
    def test_all_returns_private_groups_for_user(self, db_session, user):
        auth_group_svc = FakeAuthorityGroupService([])
        svc = ProfileGroupService(db_session, open_group_finder=auth_group_svc.public_groups)

        groups = svc.all(user)

        assert [group['id'] for group in groups] == [group.pubid for group in user.groups]

    def test_all_returns_no_private_groups_for_no_user(self, db_session):
        auth_group_svc = FakeAuthorityGroupService([])
        svc = ProfileGroupService(db_session, open_group_finder=auth_group_svc.public_groups)
        groups = svc.all(user=None)

        assert groups == []

    def test_all_returns_world_group_for_no_user(self, db_session, world_group):
        auth_group_svc = FakeAuthorityGroupService([world_group])
        svc = ProfileGroupService(db_session,
                                  open_group_finder=auth_group_svc.public_groups)

        groups = svc.all(user=None)

        assert groups[0]['id'] == world_group.pubid

    def test_all_returns_open_groups_for_no_user(self, db_session, open_groups):
        auth_group_svc = FakeAuthorityGroupService(open_groups)
        svc = ProfileGroupService(db_session,
                                  open_group_finder=auth_group_svc.public_groups)

        groups = svc.all(user=None)

        assert [group['id'] for group in groups] == [group.pubid for group in open_groups]

    def test_all_proxies_authority_parameter_to_svc(self, db_session):
        auth_group_svc = mock.Mock(spec_set=['public_groups'])
        auth_group_svc.public_groups.return_value = []
        svc = ProfileGroupService(db_session,
                                  open_group_finder=auth_group_svc.public_groups)

        groups = svc.all(user=None, authority="foo")

        auth_group_svc.public_groups.assert_called_once_with("foo")

    def test_all_includes_group_attributes(self, db_session, open_groups, user):
        auth_group_svc = FakeAuthorityGroupService(open_groups)
        svc = ProfileGroupService(db_session, open_group_finder=auth_group_svc.public_groups)

        groups = svc.all(user)

        assert 'id' in groups[0]
        assert 'name' in groups[0]
        assert 'public' in groups[0]

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

class FakeAuthorityGroupService(object):

    def __init__(self, public_groups):
        self._public_groups = public_groups

    def public_groups(self, authority):
        #return self._public_groups[authority]
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
