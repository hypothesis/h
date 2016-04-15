# -*- coding: utf-8 -*-

from mock import Mock
import pytest

from h.admin.views import badge as views


badge_index_fixtures = pytest.mark.usefixtures('models')


@badge_index_fixtures
def test_badge_index_returns_all_blocklisted_urls(models):
    assert views.badge_index(Mock()) == {
        "uris": models.Blocklist.all.return_value}


badge_add_fixtures = pytest.mark.usefixtures('models', 'badge_index')


@badge_add_fixtures
def test_badge_add_adds_uri_to_model(models):
    request = Mock(params={'add': 'test_uri'})

    views.badge_add(request)

    models.Blocklist.assert_called_once_with(uri='test_uri')
    request.db.add.assert_called_once_with(models.Blocklist.return_value)


@badge_add_fixtures
def test_badge_add_returns_index(badge_index):
    request = Mock(params={'add': 'test_uri'})

    assert views.badge_add(request) == badge_index.return_value


@badge_add_fixtures
def test_badge_add_flashes_error_if_uri_already_blocked(models):
    request = Mock(params={'add': 'test_uri'})
    models.Blocklist.side_effect = ValueError("test_error_message")

    views.badge_add(request)

    assert not request.db.add.called
    request.session.flash.assert_called_once_with(
        "test_error_message", "error")


@badge_add_fixtures
def test_badge_add_returns_index_if_uri_already_blocked(models, badge_index):
    request = Mock(params={'add': 'test_uri'})
    models.Blocklist.side_effect = ValueError("test_error_message")

    assert views.badge_add(request) == badge_index.return_value


badge_remove_fixtures = pytest.mark.usefixtures('models', 'badge_index')


@badge_remove_fixtures
def test_badge_remove_deletes_model(models):
    request = Mock(params={'remove': 'test_uri'})

    views.badge_remove(request)

    models.Blocklist.get_by_uri.assert_called_once_with('test_uri')
    request.db.delete.assert_called_once_with(
        models.Blocklist.get_by_uri.return_value)


@badge_remove_fixtures
def test_badge_remove_returns_index(badge_index):
    assert views.badge_remove(Mock(params={'remove': 'test_uri'})) == (
        badge_index.return_value)


@pytest.fixture
def badge_index(patch):
    return patch('h.admin.views.badge.badge_index')


@pytest.fixture
def models(patch):
    return patch('h.admin.views.badge.models')
