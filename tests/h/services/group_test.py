# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.models import Group
from h.models.group import JoinableBy, ReadableBy, WriteableBy
from h.services.group import GroupService
from h.services.group import groups_factory


class TestGroupService(object):
    def test_create_returns_group(self, db_session, users):
        svc = GroupService(db_session, users.get)

        group = svc.create('Anteater fans', 'foobar.com', 'cazimir')

        assert isinstance(group, Group)

    def test_create_sets_group_name(self, db_session, users):
        svc = GroupService(db_session, users.get)

        group = svc.create('Anteater fans', 'foobar.com', 'cazimir')

        assert group.name == 'Anteater fans'

    def test_create_sets_group_authority(self, db_session, users):
        svc = GroupService(db_session, users.get)

        group = svc.create('Anteater fans', 'foobar.com', 'cazimir')

        assert group.authority == 'foobar.com'

    def test_create_sets_group_creator(self, db_session, users):
        svc = GroupService(db_session, users.get)

        group = svc.create('Anteater fans', 'foobar.com', 'cazimir')

        assert group.creator == users['cazimir']

    def test_create_sets_description_when_present(self, db_session, users):
        svc = GroupService(db_session, users.get)

        group = svc.create('Anteater fans', 'foobar.com', 'cazimir', 'all about ant eaters')

        assert group.description == 'all about ant eaters'

    def test_create_skips_setting_description_when_missing(self, db_session, users):
        svc = GroupService(db_session, users.get)

        group = svc.create('Anteater fans', 'foobar.com', 'cazimir')

        assert group.description is None

    @pytest.mark.parametrize('group_type,flag,expected_value', [
        ('private', 'joinable_by', JoinableBy.authority),
        ('private', 'readable_by', ReadableBy.members),
        ('private', 'writeable_by', WriteableBy.members),
        ('publisher', 'joinable_by', None),
        ('publisher', 'readable_by', ReadableBy.world),
        ('publisher', 'writeable_by', WriteableBy.authority)])
    def test_create_sets_access_flags_for_group_types(self,
                                                      db_session,
                                                      users,
                                                      group_type,
                                                      flag,
                                                      expected_value):
        svc = GroupService(db_session, users.get)

        group = svc.create('Anteater fans', 'foobar.com', 'cazimir', type_=group_type)

        assert getattr(group, flag) == expected_value

    def test_create_raises_for_invalid_group_type(self, db_session, users):
        svc = GroupService(db_session, users.get)

        with pytest.raises(ValueError):
            svc.create('Anteater fans', 'foobar.com', 'cazimir', type_='foo')

    def test_create_adds_group_to_session(self, db_session, users):
        svc = GroupService(db_session, users.get)

        group = svc.create('Anteater fans', 'foobar.com', 'cazimir')

        assert group in db_session

    def test_create_sets_group_ids(self, db_session, users):
        svc = GroupService(db_session, users.get)

        group = svc.create('Anteater fans', 'foobar.com', 'cazimir')

        assert group.id
        assert group.pubid

    def test_create_publishes_join_event(self, db_session, users):
        publish = mock.Mock(spec_set=[])
        svc = GroupService(db_session, users.get, publish=publish)

        group = svc.create('Dishwasher disassemblers', 'foobar.com', 'theresa')

        publish.assert_called_once_with('group-join', group.pubid, 'theresa')

    def test_member_join_adds_user_to_group(self, db_session, group, users):
        svc = GroupService(db_session, users.get)

        svc.member_join(group, 'theresa')

        assert users['theresa'] in group.members

    def test_member_join_is_idempotent(self, db_session, group, users):
        svc = GroupService(db_session, users.get)

        svc.member_join(group, 'theresa')
        svc.member_join(group, 'theresa')

        assert group.members.count(users['theresa']) == 1

    def test_member_join_publishes_join_event(self, db_session, group, users):
        publish = mock.Mock(spec_set=[])
        svc = GroupService(db_session, users.get, publish=publish)
        group.pubid = 'abc123'

        svc.member_join(group, 'theresa')

        publish.assert_called_once_with('group-join', 'abc123', 'theresa')

    def test_member_leave_removes_user_from_group(self, db_session, users):
        svc = GroupService(db_session, users.get)
        group = Group(name='Theresa and her buddies',
                      authority='foobar.com',
                      creator=users['theresa'])
        group.members.append(users['cazimir'])

        svc.member_leave(group, 'cazimir')

        assert users['cazimir'] not in group.members

    def test_member_leave_is_idempotent(self, db_session, users):
        svc = GroupService(db_session, users.get)
        group = Group(name='Theresa and her buddies',
                      authority='foobar.com',
                      creator=users['theresa'])
        group.members.append(users['cazimir'])

        svc.member_leave(group, 'cazimir')
        svc.member_leave(group, 'cazimir')

        assert users['cazimir'] not in group.members

    def test_member_leave_publishes_leave_event(self, db_session, users):
        publish = mock.Mock(spec_set=[])
        svc = GroupService(db_session, users.get, publish=publish)
        group = Group(name='Donkey Trust',
                      authority='foobari.com',
                      creator=users['theresa'])
        group.members.append(users['cazimir'])
        group.pubid = 'abc123'

        svc.member_leave(group, 'cazimir')

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

    @pytest.fixture
    def group(self, users):
        return Group(name='Donkey Trust',
                     authority='foobar.com',
                     creator=users['cazimir'])

    @pytest.fixture
    def service(self, db_session, users):
        return GroupService(db_session, users.get)


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
