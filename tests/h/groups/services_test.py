# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.models import Group
from h.groups.services import GroupsService
from h.groups.services import groups_factory

from ... import factories


class TestGroupsService(object):
    def test_create_returns_group(self, db_session, users):
        svc = GroupsService(db_session, users.get)

        group = svc.create('Anteater fans', 'cazimir')

        assert isinstance(group, Group)

    def test_create_sets_group_name(self, db_session, users):
        svc = GroupsService(db_session, users.get)

        group = svc.create('Anteater fans', 'cazimir')

        assert group.name == 'Anteater fans'

    def test_create_sets_group_creator(self, db_session, users):
        svc = GroupsService(db_session, users.get)

        group = svc.create('Anteater fans', 'cazimir')

        assert group.creator == users['cazimir']

    def test_create_adds_group_to_session(self, db_session, users):
        svc = GroupsService(db_session, users.get)

        group = svc.create('Anteater fans', 'cazimir')

        assert group in db_session

    def test_create_sets_group_ids(self, db_session, users):
        svc = GroupsService(db_session, users.get)

        group = svc.create('Anteater fans', 'cazimir')

        assert group.id
        assert group.pubid

    def test_member_join_adds_user_to_group(self, db_session, users):
        svc = GroupsService(db_session, users.get)
        group = Group(name='Donkey Trust', creator=users['cazimir'])

        svc.member_join(group, 'theresa')

        assert users['theresa'] in group.members

    def test_member_join_is_idempotent(self, db_session, users):
        svc = GroupsService(db_session, users.get)
        group = Group(name='Donkey Trust', creator=users['cazimir'])

        svc.member_join(group, 'theresa')
        svc.member_join(group, 'theresa')

        assert group.members.count(users['theresa']) == 1

    def test_member_leave_removes_user_from_group(self, db_session, users):
        svc = GroupsService(db_session, users.get)
        group = Group(name='Theresa and her buddies', creator=users['theresa'])
        group.members.append(users['cazimir'])

        svc.member_leave(group, 'cazimir')

        assert users['cazimir'] not in group.members

    def test_member_leave_is_idempotent(self, db_session, users):
        svc = GroupsService(db_session, users.get)
        group = Group(name='Theresa and her buddies', creator=users['theresa'])
        group.members.append(users['cazimir'])

        svc.member_leave(group, 'cazimir')
        svc.member_leave(group, 'cazimir')

        assert users['cazimir'] not in group.members


def test_groups_factory(patch, pyramid_request):
    get_user = patch('h.groups.services.get_user')

    svc = groups_factory(None, pyramid_request)
    svc.user_fetcher('foo')

    assert isinstance(svc, GroupsService)
    assert svc.session == pyramid_request.db
    get_user.assert_called_once_with('foo', pyramid_request)


@pytest.fixture
def users():
    return {
        'cazimir': factories.User(username='cazimir'),
        'theresa': factories.User(username='theresa'),
    }
