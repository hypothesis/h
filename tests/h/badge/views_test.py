import pytest
import mock

from pyramid import httpexceptions

from h.badge import views


badge_fixtures = pytest.mark.usefixtures('models', 'search_lib')


@badge_fixtures
def test_badge_returns_number_from_search_lib(models, search_lib):
    request = mock.Mock(params={'uri': 'test_uri'})
    models.Blocklist.is_blocked.return_value = False
    search_lib.search.return_value = mock.Mock(total=29)

    result = views.badge(request)

    search_lib.search.assert_called_once_with(
        request, {'uri': 'test_uri', 'limit': 0})
    assert result == {'total': 29}


@badge_fixtures
def test_badge_returns_0_if_blocked(models, search_lib):
    request = mock.Mock(params={'uri': 'test_uri'})
    models.Blocklist.is_blocked.return_value = True
    search_lib.search.return_value = {'total': 29}

    result = views.badge(request)

    assert not search_lib.search.called
    assert result == {'total': 0}


@badge_fixtures
def test_badge_raises_if_no_uri():
    with pytest.raises(httpexceptions.HTTPBadRequest):
        views.badge(mock.Mock(params={}))


@pytest.fixture
def models(patch):
    return patch('h.badge.views.models')


@pytest.fixture
def search_lib(patch):
    return patch('h.badge.views.search_lib')
