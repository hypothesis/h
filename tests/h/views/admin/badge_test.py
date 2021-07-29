from unittest import mock

import pytest
from pyramid import httpexceptions

from h import models
from h.views.admin.badge import badge_add, badge_index, badge_remove


class TestBadgeIndex:
    def test_when_nothing_blocked(self, pyramid_request):
        result = badge_index(pyramid_request)

        assert result["uris"] == []

    def test_with_blocked_uris(self, pyramid_request, blocked_uris):
        result = badge_index(pyramid_request)

        assert set(result["uris"]) == set(blocked_uris)


@pytest.mark.usefixtures("blocked_uris", "routes")
class TestBadgeAddRemove:
    def test_add_blocks_uri(self, pyramid_request):
        pyramid_request.params = {"add": "test_uri"}

        badge_add(pyramid_request)

        assert models.Blocklist.is_blocked(pyramid_request.db, "test_uri")

    def test_add_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"add": "test_uri"}

        result = badge_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/badge"

    def test_add_flashes_error_if_uri_already_blocked(self, pyramid_request):
        pyramid_request.params = {"add": "blocked1"}
        pyramid_request.session.flash = mock.Mock()

        badge_add(pyramid_request)

        assert pyramid_request.session.flash.call_count == 1

    def test_add_redirects_to_index_if_uri_already_blocked(self, pyramid_request):
        pyramid_request.params = {"add": "blocked1"}

        result = badge_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/badge"

    def test_remove_unblocks_uri(self, pyramid_request):
        pyramid_request.params = {"remove": "blocked2"}

        badge_remove(pyramid_request)

        assert not models.Blocklist.is_blocked(pyramid_request.db, "blocked2")

    def test_remove_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"remove": "blocked1"}

        result = badge_remove(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/badge"

    def test_remove_redirects_to_index_even_if_not_blocked(self, pyramid_request):
        pyramid_request.params = {"remove": "test_uri"}

        result = badge_remove(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/badge"


@pytest.fixture
def blocked_uris(db_session):
    uris = []
    for uri in ["blocked1", "blocked2", "blocked3"]:
        uris.append(models.Blocklist(uri=uri))
    db_session.add_all(uris)
    db_session.flush()

    return uris


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("admin.badge", "/adm/badge")
