# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock
from mock import call

from pyramid import httpexceptions

from h.views.badge import badge
from h.views.badge import record_metrics


badge_fixtures = pytest.mark.usefixtures("models", "search_lib")


def test_record_metrics_records_badgenotzero_with_auth_user():
    request = mock.Mock(params={"uri": "test_uri"})
    request.user.username = "foopy"
    record_metric = mock.Mock()
    record_event = mock.Mock()
    record_metrics(1, request, record_metric=record_metric, record_event=record_event)

    record_event.assert_called_once_with(
        "BadgeNotZero", {"user": request.user.username}
    )
    record_metric.assert_called_once_with("Custom/Badge/badgeCountIsZero", 0)


def test_record_metrics_records_badgenotzero_with_unauth_user():
    request = mock.Mock(params={"uri": "test_uri"})
    request.user = None
    record_metric = mock.Mock()
    record_event = mock.Mock()
    record_metrics(1, request, record_metric=record_metric, record_event=record_event)

    record_event.assert_called_once_with("BadgeNotZero", {"user": "None"})
    record_metric.assert_called_once_with("Custom/Badge/badgeCountIsZero", 0)


def test_record_metrics_records_badgecountiszero_with_auth_user():
    request = mock.Mock(params={"uri": "test_uri"})
    record_metric = mock.Mock()
    record_event = mock.Mock()
    record_metrics(0, request, record_metric=record_metric, record_event=record_event)

    record_metric.assert_has_calls(
        [
            call("Custom/Badge/unAuthUserGotZero", 0),
            call("Custom/Badge/badgeCountIsZero", 1),
        ]
    )


def test_record_metrics_records_badgecountiszero_with_unauth_user():
    request = mock.Mock(params={"uri": "test_uri"})
    request.user = None
    record_metric = mock.Mock()
    record_event = mock.Mock()
    record_metrics(0, request, record_metric=record_metric, record_event=record_event)

    record_metric.assert_has_calls(
        [
            call("Custom/Badge/unAuthUserGotZero", 1),
            call("Custom/Badge/badgeCountIsZero", 1),
        ]
    )


@badge_fixtures
def test_badge_returns_number_from_search(models, search_run):
    request = mock.Mock(params={"uri": "test_uri"})
    models.Blocklist.is_blocked.return_value = False
    search_run.return_value = mock.Mock(total=29)

    result = badge(request)

    search_run.assert_called_once_with({"uri": "test_uri", "limit": 0})
    assert result == {"total": 29}


@badge_fixtures
def test_badge_returns_0_if_blocked(models, search_run):
    request = mock.Mock(params={"uri": "test_uri"})
    models.Blocklist.is_blocked.return_value = True
    search_run.return_value = {"total": 29}

    result = badge(request)

    assert not search_run.called
    assert result == {"total": 0}


@badge_fixtures
def test_badge_raises_if_no_uri():
    with pytest.raises(httpexceptions.HTTPBadRequest):
        badge(mock.Mock(params={}))


@pytest.fixture
def models(patch):
    return patch("h.views.badge.models")


@pytest.fixture
def search_lib(patch):
    return patch("h.views.badge.search")


@pytest.fixture
def search_run(search_lib):
    return search_lib.Search.return_value.run
