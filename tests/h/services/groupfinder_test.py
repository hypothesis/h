# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services.groupfinder import groupfinder_service_factory
from h.services.groupfinder import GroupfinderService


class TestGroupfinderService(object):
    def test_returns_correct_group(self, svc, factories):
        group = factories.Group()

        assert svc.find(group.pubid) == group

    def test_sets_authority_on_world_group(self, svc):
        group = svc.find("__world__")

        assert group.authority == "example.com"

    def test_returns_none_when_not_found(self, svc, factories):
        factories.Group()

        assert svc.find("bogus") is None

    @pytest.fixture
    def svc(self, db_session):
        return GroupfinderService(db_session, "example.com")


class TestGroupfinderServiceFactory(object):
    def test_returns_groupfinder_service(self, pyramid_request):
        svc = groupfinder_service_factory(None, pyramid_request)

        assert isinstance(svc, GroupfinderService)

    def test_provides_database_session(self, pyramid_request):
        svc = groupfinder_service_factory(None, pyramid_request)

        assert svc.session == pyramid_request.db

    def test_provides_authority(self, pyramid_request):
        svc = groupfinder_service_factory(None, pyramid_request)

        assert svc.authority == pyramid_request.default_authority
