# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.models import User, GroupScope
from h.models.group import ReadableBy
from h.services.group import GroupService
from h.services.group import groups_factory
from h.services.user import UserService
from tests.common.matchers import Matcher


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


@pytest.fixture
def usr_svc(pyramid_request, db_session):
    def fetch(userid):
        # One doesn't want to couple to the user fetching service but
        # we do want to be able to fetch user models for internal
        # module behavior tests
        return db_session.query(User).filter_by(userid=userid).one_or_none()
    return fetch


@pytest.fixture
def svc(db_session, usr_svc):
    return GroupService(db_session, usr_svc)


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
