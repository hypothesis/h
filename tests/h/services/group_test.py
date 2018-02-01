# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.models import Group
from h.models.group import JoinableBy, ReadableBy, WriteableBy
from h.services.group import GroupService
from h.services.group import groups_factory


class TestGroupService(object):
    def test_create_returns_group(self, service):
        group = service.create('Anteater fans', 'cazimir')

        assert isinstance(group, Group)

    def test_create_sets_group_name(self, service):
        group = service.create('Anteater fans', 'cazimir')

        assert group.name == 'Anteater fans'

    def test_create_sets_group_authority(self, service):
        group = service.create('Anteater fans', 'cazimir')

        assert group.authority == 'example.com'

    def test_create_sets_group_creator(self, service, users):
        group = service.create('Anteater fans', 'cazimir')

        assert group.creator == users['cazimir']

    def test_create_sets_description_when_present(self, service):
        group = service.create('Anteater fans', 'cazimir', 'all about ant eaters')

        assert group.description == 'all about ant eaters'

    def test_create_skips_setting_description_when_missing(self, service):
        group = service.create('Anteater fans', 'cazimir')

        assert group.description is None

    def test_create_adds_group_creator_to_members(self, service, users):
        group = service.create('Anteater fans', 'cazimir')

        assert users['cazimir'] in group.members

    def test_create_doesnt_add_group_creator_to_members_for_open_groups(self, service, users):
        group = service.create_open_group('Anteater fans', 'cazimir')

        assert users['cazimir'] not in group.members

    @pytest.mark.parametrize('flag,expected_value', [
        ('joinable_by', JoinableBy.authority),
        ('readable_by', ReadableBy.members),
        ('writeable_by', WriteableBy.members)])
    def test_create_sets_access_flags(self, service, flag, expected_value):
        group = service.create('Anteater fans', 'cazimir')

        assert getattr(group, flag) == expected_value

    def test_create_adds_group_to_session(self, db_session, service):
        group = service.create('Anteater fans', 'cazimir')

        assert group in db_session

    def test_create_sets_group_ids(self, service):
        group = service.create('Anteater fans', 'cazimir')

        assert group.id
        assert group.pubid

    def test_create_publishes_join_event(self, service, publish):
        group = service.create('Dishwasher disassemblers', 'theresa')

        publish.assert_called_once_with('group-join', group.pubid, 'acct:theresa@example.com')

    def test_create_open_group_returns_group(self, service, users):
        creator = users['cazimir']

        group = service.create_open_group(name='test_group',
                                          userid=creator.username,
                                          description='test_description')

        assert group.name == 'test_group'
        assert group.authority == 'example.com'
        assert group.creator == creator
        assert group.description == 'test_description'
        assert group.joinable_by is None
        assert group.readable_by == ReadableBy.world
        assert group.writeable_by == WriteableBy.authority

    def test_create_open_group_description_defaults_to_None(self, service):
        # Create a group with no `description` argument.
        group = service.create_open_group(name='test_group', userid='cazimir')

        assert group.description is None

    def test_member_join_adds_user_to_group(self, service, group, users):
        service.member_join(group, 'theresa')

        assert users['theresa'] in group.members

    def test_member_join_is_idempotent(self, service, group, users):
        service.member_join(group, 'theresa')
        service.member_join(group, 'theresa')

        assert group.members.count(users['theresa']) == 1

    def test_member_join_publishes_join_event(self, service, publish, group):
        group.pubid = 'abc123'

        service.member_join(group, 'theresa')

        publish.assert_called_once_with('group-join', 'abc123', 'theresa')

    def test_member_leave_removes_user_from_group(self, service, users):
        group = Group(name='Theresa and her buddies',
                      authority='foobar.com',
                      creator=users['theresa'])
        group.members.append(users['cazimir'])

        service.member_leave(group, 'cazimir')

        assert users['cazimir'] not in group.members

    def test_member_leave_is_idempotent(self, service, users):
        group = Group(name='Theresa and her buddies',
                      authority='foobar.com',
                      creator=users['theresa'])
        group.members.append(users['cazimir'])

        service.member_leave(group, 'cazimir')
        service.member_leave(group, 'cazimir')

        assert users['cazimir'] not in group.members

    def test_member_leave_publishes_leave_event(self, service, users, publish):
        group = Group(name='Donkey Trust',
                      authority='foobari.com',
                      creator=users['theresa'])
        group.members.append(users['cazimir'])
        group.pubid = 'abc123'

        service.member_leave(group, 'cazimir')

        publish.assert_called_once_with('group-leave', 'abc123', 'cazimir')

    @pytest.mark.parametrize('with_user', [True, False])
    def test_groupids_readable_by_includes_world(self, with_user, service, db_session, factories):
        user = None
        if with_user:
            user = factories.User()
            db_session.flush()

        assert '__world__' in service.groupids_readable_by(user)

    @pytest.mark.parametrize('with_user', [True, False])
    def test_groupids_readable_by_includes_world_readable_groups(self, with_user, service, db_session, factories):
        # group readable by members
        factories.Group(readable_by=ReadableBy.members)
        # group readable by everyone
        group = factories.Group(readable_by=ReadableBy.world)

        user = None
        if with_user:
            user = factories.User()
            db_session.flush()

        assert group.pubid in service.groupids_readable_by(user)

    def test_groupids_readable_by_includes_memberships(self, service, db_session, factories):
        user = factories.User()

        group = factories.Group(readable_by=ReadableBy.members)
        group.members.append(user)

        db_session.flush()

        assert group.pubid in service.groupids_readable_by(user)

    def test_groupids_created_by_includes_created_groups(self, service, factories):
        user = factories.User()
        group = factories.Group(creator=user)

        assert group.pubid in service.groupids_created_by(user)

    def test_groupids_created_by_excludes_other_groups(self, service, db_session, factories):
        user = factories.User()
        private_group = factories.Group()
        private_group.members.append(user)
        factories.Group(readable_by=ReadableBy.world)
        db_session.flush()

        assert service.groupids_created_by(user) == []

    def test_groupids_created_by_returns_empty_list_for_missing_user(self, service):
        assert service.groupids_created_by(None) == []

    @pytest.fixture
    def group(self, users):
        return Group(name='Donkey Trust',
                     authority='foobar.com',
                     creator=users['cazimir'])

    @pytest.fixture
    def publish(self):
        return mock.Mock(spec_set=[])

    @pytest.fixture
    def service(self, db_session, users, publish):
        return GroupService(db_session, users.get, publish=publish)


@pytest.mark.usefixtures('user_service')
class TestGroupsFactory(object):
    def test_returns_groups_service(self, pyramid_request):
        svc = groups_factory(None, pyramid_request)

        assert isinstance(svc, GroupService)

    def test_provides_request_db_as_session(self, pyramid_request):
        svc = groups_factory(None, pyramid_request)

        assert svc.session == pyramid_request.db

    def test_wraps_user_service_as_user_fetcher(self, pyramid_request, user_service):
        svc = groups_factory(None, pyramid_request)

        svc.user_fetcher('foo')

        user_service.fetch.assert_called_once_with('foo')

    def test_provides_realtime_publisher_as_publish(self, patch, pyramid_request):
        pyramid_request.realtime = mock.Mock(spec_set=['publish_user'])
        session = patch('h.services.group.session')
        svc = groups_factory(None, pyramid_request)

        svc.publish('group-join', 'abc123', 'theresa')

        session.model.assert_called_once_with(pyramid_request)
        pyramid_request.realtime.publish_user.assert_called_once_with({
            'type': 'group-join',
            'session_model': session.model.return_value,
            'userid': 'theresa',
            'group': 'abc123',
        })


@pytest.fixture
def user_service(pyramid_config):
    service = mock.Mock(spec_set=['fetch'])
    service.fetch.return_value = None
    pyramid_config.register_service(service, name='user')
    return service


@pytest.fixture
def users(factories):
    return {
        'cazimir': factories.User(username='cazimir'),
        'theresa': factories.User(username='theresa'),
    }
