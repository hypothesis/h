# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.groups.util import WorldGroup
from h.services.groupfinder import groupfinder_service_factory
from h.services.groupfinder import GroupfinderService


class TestGroupfinderService(object):
    def test_returns_correct_group(self, svc, factories):
        group = factories.Group()

        assert svc.find(group.pubid) == group

    def test_returns_correct_group_for_world(self, svc):
        group = svc.find('__world__')

        assert isinstance(group, WorldGroup)

    def test_sets_auth_domain_on_world_group(self, svc):
        group = svc.find('__world__')

        assert group.auth_domain == 'example.com'

    def test_returns_none_when_not_found(self, svc, factories):
        factories.Group()

        assert svc.find('bogus') is None

    def test_caches_groups(self, svc, factories, db_session):
        group = factories.Group()
        pubid = group.pubid

        svc.find(group.pubid)
        db_session.delete(group)
        db_session.flush()
        group = svc.find(pubid)

        assert group is not None
        assert group.pubid == pubid

    def test_sets_up_cache_clearing_on_transaction_end(self, patch, db_session):
        decorator = patch('h.services.groupfinder.util.db.on_transaction_end')

        GroupfinderService(db_session, 'example.com')

        decorator.assert_called_once_with(db_session)

    def test_clears_cache_on_transaction_end(self, patch, db_session, factories):
        funcs = {}

        # We need to capture the inline `clear_cache` function so we can
        # call it manually later
        def on_transaction_end_decorator(session):
            def on_transaction_end(func):
                funcs['clear_cache'] = func
            return on_transaction_end

        decorator = patch('h.services.user.util.db.on_transaction_end')
        decorator.side_effect = on_transaction_end_decorator

        group = factories.Group()
        pubid = group.pubid
        svc = GroupfinderService(db_session, 'example.com')
        svc.find(pubid)
        db_session.delete(group)

        funcs['clear_cache']()

        group = svc.find(pubid)
        assert group is None

    @pytest.fixture
    def svc(self, db_session):
        return GroupfinderService(db_session, 'example.com')


class TestGroupfinderServiceFactory(object):
    def test_returns_groupfinder_service(self, pyramid_request):
        svc = groupfinder_service_factory(None, pyramid_request)

        assert isinstance(svc, GroupfinderService)

    def test_provides_database_session(self, pyramid_request):
        svc = groupfinder_service_factory(None, pyramid_request)

        assert svc.session == pyramid_request.db

    def test_provides_auth_domain(self, pyramid_request):
        svc = groupfinder_service_factory(None, pyramid_request)

        assert svc.auth_domain == pyramid_request.auth_domain
