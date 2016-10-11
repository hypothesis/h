# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from pyramid import httpexceptions

from h.views.badge import badge


badge_fixtures = pytest.mark.usefixtures('models', 'search_lib')


@badge_fixtures
def test_badge_returns_number_from_search(models, search_run):
    request = mock.Mock(params={'uri': 'test_uri'})
    models.Blocklist.is_blocked.return_value = False
    search_run.return_value = mock.Mock(total=29)

    result = badge(request)

    search_run.assert_called_once_with({'uri': 'test_uri', 'limit': 0})
    assert result == {'total': 29}


@badge_fixtures
def test_badge_returns_0_if_blocked(models, search_run):
    request = mock.Mock(params={'uri': 'test_uri'})
    models.Blocklist.is_blocked.return_value = True
    search_run.return_value = {'total': 29}

    result = badge(request)

    assert not search_run.called
    assert result == {'total': 0}


@badge_fixtures
def test_badge_raises_if_no_uri():
    with pytest.raises(httpexceptions.HTTPBadRequest):
        badge(mock.Mock(params={}))


@pytest.fixture
def models(patch):
    return patch('h.views.badge.models')


@pytest.fixture
def search_lib(patch):
    return patch('h.views.badge.search')


@pytest.fixture
def search_run(search_lib):
    return search_lib.Search.return_value.run
