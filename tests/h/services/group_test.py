# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.models import Group, User, GroupScope
from h.models.group import JoinableBy, ReadableBy, WriteableBy
from h.services.group import GroupService
from h.services.group import groups_factory
from h.services.user import UserService
from tests.common.matchers import Matcher


class TestGroupServiceCreatePrivateGroup(object):
    """Unit tests for :py:meth:`GroupService.create_private_group`"""

    def test_it_returns_group_model(self, creator, svc):
        group = svc.create_private_group('Anteater fans', creator.userid)

        assert isinstance(group, Group)

    def test_it_sets_group_name(self, creator, svc):
        group = svc.create_private_group('Anteater fans', creator.userid)

        assert group.name == 'Anteater fans'

    def test_it_sets_group_authority(self, svc, creator, pyramid_request):
        group = svc.create_private_group('Anteater fans', creator.userid)

        assert group.authority == pyramid_request.authority

    def test_it_sets_group_creator(self, svc, creator):
        group = svc.create_private_group('Anteater fans', creator.userid)

        assert group.creator == creator

    def test_it_sets_description_when_present(self, svc, creator):
        group = svc.create_private_group('Anteater fans', creator.userid, 'all about ant eaters')

        assert group.description == 'all about ant eaters'

    def test_it_skips_setting_description_when_missing(self, svc, creator):
        group = svc.create_private_group('Anteater fans', creator.userid)

        assert group.description is None

    def test_it_adds_group_creator_to_members(self, svc, creator):
        group = svc.create_private_group('Anteater fans', creator.userid)

        assert creator in group.members

    @pytest.mark.parametrize('flag,expected_value', [
        ('joinable_by', JoinableBy.authority),
        ('readable_by', ReadableBy.members),
        ('writeable_by', WriteableBy.members)])
    def test_it_sets_access_flags(self, svc, creator, flag, expected_value):
        group = svc.create_private_group('Anteater fans', creator.userid)

        assert getattr(group, flag) == expected_value

    def test_it_creates_group_with_default_organization(
            self, default_organization, creator, svc):
        group = svc.create_private_group('Anteater fans', creator.userid)

        assert group.organization == default_organization

    def test_it_creates_group_with_specified_organization(self, factories, creator, svc):
        org = factories.Organization()

        group = svc.create_private_group('Anteater fans', creator.userid, organization=org)

        assert group.organization == org

    def test_it_adds_group_to_session(self, db_session, creator, svc):
        group = svc.create_private_group('Anteater fans', creator.userid)

        assert group in db_session

    def test_it_sets_group_ids(self, creator, svc):
        group = svc.create_private_group('Anteater fans', creator.userid)

        assert group.id
        assert group.pubid

    def test_it_publishes_join_event(self, svc, creator, publish):
        group = svc.create_private_group('Dishwasher disassemblers', creator.userid)

        publish.assert_called_once_with('group-join', group.pubid, creator.userid)


class TestGroupServiceCreateOpenGroup(object):
    """Unit tests for :py:meth:`GroupService.create_open_group`"""

    def test_it_returns_group_model(self, creator, svc, origins):
        group = svc.create_open_group('Anteater fans', creator.userid, origins=origins)

        assert isinstance(group, Group)

    @pytest.mark.parametrize('group_attr,expected_value', [
        ('name', 'test group'),
        ('description', 'test description'),
        ('authority', 'example.com')
    ])
    def test_it_creates_group_attrs(self, creator, svc, origins, group_attr, expected_value):
        group = svc.create_open_group('test group', creator.userid, origins=origins, description='test description')

        assert getattr(group, group_attr) == expected_value

    def test_it_skips_setting_description_when_missing(self, svc, creator, origins):
        group = svc.create_open_group('Anteater fans', creator.userid, origins=origins)

        assert group.description is None

    def test_it_sets_group_creator(self, svc, creator, origins):
        group = svc.create_open_group('Anteater fans', creator.userid, origins=origins)

        assert group.creator == creator

    def test_it_does_not_add_group_creator_to_members(self, svc, creator, origins):
        group = svc.create_open_group('Anteater fans', creator.userid, origins=origins)

        assert creator not in group.members

    @pytest.mark.parametrize('flag,expected_value', [
        ('joinable_by', None),
        ('readable_by', ReadableBy.world),
        ('writeable_by', WriteableBy.authority)])
    def test_it_sets_access_flags(self, svc, creator, origins, flag, expected_value):
        group = svc.create_open_group('Anteater fans', creator.userid, origins=origins)

        assert getattr(group, flag) == expected_value

    def test_it_creates_group_with_default_organization(
            self, default_organization, creator, svc, origins):
        group = svc.create_open_group('Anteater fans', creator.userid, origins=origins)

        assert group.organization == default_organization

    def test_it_creates_group_with_specified_organization(self, factories, creator, svc, origins):
        org = factories.Organization()

        group = svc.create_open_group('Anteater fans', creator.userid, origins=origins, organization=org)

        assert group.organization == org

    def test_it_adds_group_to_session(self, db_session, creator, svc, origins):
        group = svc.create_open_group('Anteater fans', creator.userid, origins=origins)

        assert group in db_session

    def test_it_does_not_publish_join_event(self, svc, creator, publish, origins):
        svc.create_open_group('Dishwasher disassemblers', creator.userid, origins=origins)

        publish.assert_not_called()

    def test_it_sets_scopes(self, svc, matchers, creator):
        origins = ['https://biopub.org', 'http://example.com', 'https://wikipedia.com']

        group = svc.create_open_group(name='test_group', userid=creator.userid, origins=origins)

        assert group.scopes == matchers.UnorderedList([
            GroupScopeWithOrigin(h) for h in origins])

    def test_it_always_creates_new_scopes(self, db_session, factories, svc, creator, matchers):
        # It always creates a new scope, even if a scope with the given origin
        # already exists (this is because a single scope can only belong to
        # one group, so the existing scope can't be reused with the new group).
        origins = ['https://biopub.org', 'http://example.com']
        scopes = [factories.GroupScope(origin=h) for h in origins]

        group = svc.create_open_group(name='test_group', userid=creator.userid, origins=origins)
        for scope in scopes:
            assert scope not in group.scopes


class TestGroupServiceCreateRestrictedGroup(object):
    """Unit tests for :py:meth:`GroupService.create_restricted_group`"""

    def test_it_returns_group_model(self, creator, svc, origins):
        group = svc.create_restricted_group('Anteater fans', creator.userid, origins=origins)

        assert isinstance(group, Group)

    @pytest.mark.parametrize('group_attr,expected_value', [
        ('name', 'test group'),
        ('description', 'test description'),
        ('authority', 'example.com')
    ])
    def test_it_creates_group_attrs(self, creator, svc, origins, group_attr, expected_value):
        group = svc.create_restricted_group('test group', creator.userid, origins=origins, description='test description')

        assert getattr(group, group_attr) == expected_value

    def test_it_skips_setting_description_when_missing(self, svc, creator, origins):
        group = svc.create_restricted_group('Anteater fans', creator.userid, origins=origins)

        assert group.description is None

    def test_it_sets_group_creator(self, svc, creator, origins):
        group = svc.create_restricted_group('Anteater fans', creator.userid, origins=origins)

        assert group.creator == creator

    def test_it_adds_group_creator_to_members(self, svc, creator, origins):
        group = svc.create_restricted_group('Anteater fans', creator.userid, origins=origins)

        assert creator in group.members

    @pytest.mark.parametrize('flag,expected_value', [
        ('joinable_by', None),
        ('readable_by', ReadableBy.world),
        ('writeable_by', WriteableBy.members)])
    def test_it_sets_access_flags(self, svc, creator, origins, flag, expected_value):
        group = svc.create_restricted_group('Anteater fans', creator.userid, origins=origins)

        assert getattr(group, flag) == expected_value

    def test_it_creates_group_with_default_organization(
            self, default_organization, creator, svc, origins):
        group = svc.create_restricted_group('Anteater fans', creator.userid, origins=origins)

        assert group.organization == default_organization

    def test_it_creates_group_with_specified_organization(self, factories, creator, svc, origins):
        org = factories.Organization()

        group = svc.create_restricted_group('Anteater fans', creator.userid, origins=origins, organization=org)

        assert group.organization == org

    def test_it_adds_group_to_session(self, db_session, creator, svc, origins):
        group = svc.create_restricted_group('Anteater fans', creator.userid, origins=origins)

        assert group in db_session

    def test_it_publishes_join_event(self, svc, creator, publish, origins):
        group = svc.create_restricted_group('Dishwasher disassemblers', creator.userid, origins=origins)

        publish.assert_called_once_with('group-join', group.pubid, creator.userid)

    def test_it_sets_scopes(self, svc, matchers, creator):
        origins = ['https://biopub.org', 'http://example.com', 'https://wikipedia.com']

        group = svc.create_restricted_group(name='test_group', userid=creator.userid, origins=origins)

        assert group.scopes == matchers.UnorderedList([
            GroupScopeWithOrigin(h) for h in origins])

    def test_it_with_mismatched_authorities_raises_value_error(
            self, db_session, svc, origins, creator, factories):
        org = factories.Organization(
            name='My organization',
            authority='bar.com',
            )
        with pytest.raises(ValueError):
            svc.create_restricted_group(name='test_group',
                                        userid=creator.userid,
                                        origins=origins,
                                        description='test_description',
                                        organization=org)

    def test_it_always_creates_new_scopes(self, db_session, factories, svc, creator, matchers):
        # It always creates a new scope, even if a scope with the given origin
        # already exists (this is because a single scope can only belong to
        # one group, so the existing scope can't be reused with the new group).
        origins = ['https://biopub.org', 'http://example.com']
        scopes = [factories.GroupScope(origin=h) for h in origins]

        group = svc.create_restricted_group(name='test_group',
                                            userid=creator.userid,
                                            origins=origins)

        for scope in scopes:
            assert scope not in group.scopes


class TestGroupServiceMemberJoin(object):
    """Unit tests for :py:meth:`GroupService.member_join`"""

    def test_it_adds_user_to_group(self, svc, factories):
        user = factories.User()
        group = factories.Group()
        svc.member_join(group, user.userid)

        assert user in group.members

    def test_it_is_idempotent(self, svc, factories):
        user = factories.User()
        group = factories.Group()
        svc.member_join(group, user.userid)
        svc.member_join(group, user.userid)

        assert group.members.count(user) == 1

    def test_it_publishes_join_event(self, svc, factories, publish):
        group = factories.Group()
        user = factories.User()

        svc.member_join(group, user.userid)

        publish.assert_called_once_with('group-join', group.pubid, user.userid)


class TestGroupServiceMemberLeave(object):
    """Unit tests for :py:meth:`GroupService.member_leave`"""

    def test_it_removes_user_from_group(self, svc, factories, creator):
        group = factories.Group(creator=creator)
        new_member = factories.User()
        group.members.append(new_member)

        svc.member_leave(group, new_member.userid)

        assert new_member not in group.members

    def test_it_is_idempotent(self, svc, factories, creator):
        group = factories.Group(creator=creator)
        new_member = factories.User()
        group.members.append(new_member)

        svc.member_leave(group, new_member.userid)
        svc.member_leave(group, new_member.userid)

        assert new_member not in group.members

    def test_it_publishes_leave_event(self, svc, factories, publish):
        group = factories.Group()
        new_member = factories.User()
        group.members.append(new_member)

        svc.member_leave(group, new_member.userid)

        publish.assert_called_once_with('group-leave', group.pubid, new_member.userid)


class TestGroupServiceAddMembers(object):
    """Unit tests for :py:meth:`GroupService.add_members`"""

    def test_it_adds_users_in_userids(self, factories, svc):
        group = factories.OpenGroup()
        users = [factories.User(), factories.User()]
        userids = [user.userid for user in users]

        svc.add_members(group, userids)

        assert group.members == users

    def test_it_does_not_remove_existing_members(self, factories, svc):
        creator = factories.User()
        group = factories.Group(creator=creator)
        users = [factories.User(), factories.User()]
        userids = [user.userid for user in users]

        svc.add_members(group, userids)

        assert len(group.members) == len(users) + 1  # account for creator user
        assert creator in group.members


class TestGroupServiceUpdateMembers(object):
    """Unit tests for :py:meth:`GroupService.update_members`"""

    def test_it_adds_users_in_userids(self, factories, svc):
        group = factories.OpenGroup()  # no members at outset
        new_members = [
            factories.User(),
            factories.User()
        ]

        svc.update_members(group, [user.userid for user in new_members])

        assert group.members == new_members

    def test_it_removes_members_not_present_in_userids(self, factories, svc, creator):
        group = factories.Group(creator=creator)  # creator will be a member
        new_members = [
            factories.User(),
            factories.User()
        ]
        group.members.append(new_members[0])
        group.members.append(new_members[1])

        svc.update_members(group, [])

        assert not group.members  # including the creator

    def test_it_does_not_remove_members_present_in_userids(self, factories, svc, publish):
        group = factories.OpenGroup()  # no members at outset
        new_members = [
            factories.User(),
            factories.User()
        ]
        group.members.append(new_members[0])
        group.members.append(new_members[1])

        svc.update_members(group, [user.userid for user in group.members])

        assert new_members[0] in group.members
        assert new_members[1] in group.members
        publish.assert_not_called()

    def test_it_proxies_to_member_join_and_leave(self, factories, svc):
        svc.member_join = mock.Mock()
        svc.member_leave = mock.Mock()

        group = factories.OpenGroup()  # no members at outset
        new_members = [
            factories.User(),
            factories.User()
        ]
        group.members.append(new_members[0])

        svc.update_members(group, [new_members[1].userid])

        svc.member_join.assert_called_once_with(group, new_members[1].userid)
        svc.member_leave.assert_called_once_with(group, new_members[0].userid)

    def test_it_does_not_add_duplicate_members(self, factories, svc):
        # test for idempotency
        group = factories.OpenGroup()
        new_member = factories.User()

        svc.update_members(group, [new_member.userid, new_member.userid])

        assert group.members == [new_member]
        assert len(group.members) == 1


class TestGroupServiceGroupIds(object):
    """Unit tests for methods related to group IDs:
        - :py:meth:`GroupService.groupids_readable_by`
        - :py:meth:`GroupService.groupids_created_by`
    """

    @pytest.mark.parametrize('with_user', [True, False])
    def test_readable_by_includes_world(self, with_user, svc, db_session, factories):
        user = None
        if with_user:
            user = factories.User()
            db_session.flush()

        assert '__world__' in svc.groupids_readable_by(user)

    @pytest.mark.parametrize('with_user', [True, False])
    def test_readable_by_includes_world_readable_groups(self, with_user, svc, db_session, factories):
        # group readable by members
        factories.Group(readable_by=ReadableBy.members)
        # group readable by everyone
        group = factories.Group(readable_by=ReadableBy.world)

        user = None
        if with_user:
            user = factories.User()
            db_session.flush()

        assert group.pubid in svc.groupids_readable_by(user)

    def test_readable_by_includes_memberships(self, svc, db_session, factories):
        user = factories.User()

        group = factories.Group(readable_by=ReadableBy.members)
        group.members.append(user)

        db_session.flush()

        assert group.pubid in svc.groupids_readable_by(user)

    def test_created_by_includes_created_groups(self, svc, factories):
        user = factories.User()
        group = factories.Group(creator=user)

        assert group.pubid in svc.groupids_created_by(user)

    def test_created_by_excludes_other_groups(self, svc, db_session, factories):
        user = factories.User()
        private_group = factories.Group()
        private_group.members.append(user)
        factories.Group(readable_by=ReadableBy.world)
        db_session.flush()

        assert svc.groupids_created_by(user) == []

    def test_created_by_returns_empty_list_for_missing_user(self, svc):
        assert svc.groupids_created_by(None) == []


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
def usr_svc(pyramid_request, db_session):
    def fetch(userid):
        # One doesn't want to couple to the user fetching service but
        # we do want to be able to fetch user models for internal
        # module behavior tests
        return db_session.query(User).filter_by(userid=userid).one_or_none()
    return fetch


@pytest.fixture
def origins():
    return ['http://example.com']


@pytest.fixture
def publish():
    return mock.Mock(spec_set=[])


@pytest.fixture
def svc(db_session, usr_svc, publish):
    return GroupService(db_session, usr_svc, publish=publish)


@pytest.fixture
def creator(factories):
    return factories.User(username='group_creator')


@pytest.fixture
def user_service(pyramid_config):
    service = mock.create_autospec(UserService, spec_set=True, instance=True)
    pyramid_config.register_service(service, name='user')
    return service


class GroupScopeWithOrigin(Matcher):
    """Matches any GroupScope with the given origin."""

    def __init__(self, origin):
        self.origin = origin

    def __eq__(self, group_scope):
        if not isinstance(group_scope, GroupScope):
            return False
        return group_scope.origin == self.origin
