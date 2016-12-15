# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.groups import search
from h.models.group import ReadableBy


class TestGroupAuthFilter(object):
    @pytest.mark.parametrize('is_authenticated', [True, False])
    def test_filter_includes_world_group(self, pyramid_request, factories, is_authenticated):
        if is_authenticated:
            pyramid_request.authenticated_user = factories.User()

        filter_ = search.GroupAuthFilter(pyramid_request)

        filtered_groups = filter_(None)['terms']['group']
        assert '__world__' in filtered_groups

    @pytest.mark.parametrize('is_authenticated', [True, False])
    def test_filter_includes_world_readable_groups(
            self, pyramid_request, db_session, factories, is_authenticated):
        group_1 = factories.Group(readable_by=ReadableBy.members)
        group_2 = factories.Group(readable_by=ReadableBy.world)
        group_3 = factories.Group(readable_by=ReadableBy.members)
        group_4 = factories.Group(readable_by=ReadableBy.world)
        db_session.add_all([group_1, group_2])

        if is_authenticated:
            user = factories.User()
            db_session.add(user)
            pyramid_request.authenticated_user = user

        filter_ = search.GroupAuthFilter(pyramid_request)

        filtered_groups = filter_(None)['terms']['group']
        assert group_1.pubid not in filtered_groups
        assert group_3.pubid not in filtered_groups
        assert group_2.pubid in filtered_groups
        assert group_4.pubid in filtered_groups

    def test_filter_includes_group_memberships(self, pyramid_request, db_session, factories):
        user = factories.User()
        group_1 = factories.Group(creator=user)
        group_2 = factories.Group()
        group_3 = factories.Group()
        group_3.members.append(user)
        db_session.add_all([user, group_1, group_2, group_3])
        db_session.flush()

        pyramid_request.authenticated_user = user
        filter_ = search.GroupAuthFilter(pyramid_request)

        filtered_groups = filter_(None)['terms']['group']
        assert group_1.pubid in filtered_groups
        assert group_3.pubid in filtered_groups
        assert group_2.pubid not in filtered_groups

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.authenticated_user = None
        return pyramid_request

    @pytest.fixture
    def user(self, db_session, factories):
        user = factories.User()
        db_session.add(user)
        db_session.flush()
        return user
