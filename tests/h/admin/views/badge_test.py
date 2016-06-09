# -*- coding: utf-8 -*-

import mock
import pytest
from pyramid import httpexceptions
from pyramid.testing import DummyRequest

from h import models
from h.admin.views import badge as views


class TestBadgeIndex(object):
    def test_when_nothing_blocked(self, req):
        result = views.badge_index(req)

        assert result["uris"] == []

    def test_with_blocked_uris(self, req, blocked_uris):
        result = views.badge_index(req)

        assert set(result["uris"]) == set(blocked_uris)


@pytest.mark.usefixtures('blocked_uris', 'routes')
class TestBadgeAddRemove(object):
    def test_add_blocks_uri(self, req):
        req.params = {'add': 'test_uri'}

        views.badge_add(req)

        assert models.Blocklist.is_blocked(req.db, 'test_uri')

    def test_add_redirects_to_index(self, req):
        req.params = {'add': 'test_uri'}

        result = views.badge_add(req)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/badge'

    def test_add_flashes_error_if_uri_already_blocked(self, req):
        req.params = {'add': 'blocked1'}
        req.session.flash = mock.Mock()

        views.badge_add(req)

        assert req.session.flash.call_count == 1

    def test_add_redirects_to_index_if_uri_already_blocked(self, req):
        req.params = {'add': 'blocked1'}

        result = views.badge_add(req)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/badge'

    def test_remove_unblocks_uri(self, req):
        req.params = {'remove': 'blocked2'}

        views.badge_remove(req)

        assert not models.Blocklist.is_blocked(req.db, 'blocked2')

    def test_remove_redirects_to_index(self, req):
        req.params = {'remove': 'blocked1'}

        result = views.badge_remove(req)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/badge'

    def test_remove_redirects_to_index_even_if_not_blocked(self, req):
        req.params = {'remove': 'test_uri'}

        result = views.badge_remove(req)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/badge'


@pytest.fixture
def blocked_uris(db_session):
    from h import models

    uris = []
    for uri in ['blocked1', 'blocked2', 'blocked3']:
        uris.append(models.Blocklist(uri=uri))
    db_session.add_all(uris)
    db_session.flush()

    return uris


@pytest.fixture
def req(db_session):
    return DummyRequest(db=db_session)


@pytest.fixture
def routes(config):
    config.add_route('admin_badge', '/adm/badge')
