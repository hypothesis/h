# -*- coding: utf-8 -*-

import mock
import pytest

from h.streamer import views
from h.streamer import streamer


def test_websocket_view_bad_origin(pyramid_request):
    pyramid_request.registry.settings.update({'origins': ['http://good']})
    pyramid_request.headers = {'Origin': 'http://bad'}
    res = views.websocket_view(pyramid_request)
    assert res.code == 403


def test_websocket_view_good_origin(pyramid_request):
    pyramid_request.registry.settings.update({'origins': ['http://good']})
    pyramid_request.headers = {'Origin': 'http://good'}
    pyramid_request.get_response = lambda _: mock.sentinel.good_response
    res = views.websocket_view(pyramid_request)
    assert res == mock.sentinel.good_response


def test_websocket_view_same_origin(pyramid_request):
    pyramid_request.get_response = lambda _: mock.sentinel.good_response
    res = views.websocket_view(pyramid_request)
    assert res == mock.sentinel.good_response


def test_websocket_view_adds_auth_state_to_environ(pyramid_config, pyramid_request):
    pyramid_config.testing_securitypolicy('ragnar', groupids=['foo', 'bar'])
    pyramid_request.get_response = lambda _: None

    views.websocket_view(pyramid_request)
    env = pyramid_request.environ

    assert env['h.ws.authenticated_userid'] == 'ragnar'
    assert env['h.ws.effective_principals'] == pyramid_request.effective_principals


def test_websocket_view_adds_registry_reference_to_environ(pyramid_request):
    pyramid_request.get_response = lambda _: None

    views.websocket_view(pyramid_request)
    env = pyramid_request.environ

    assert env['h.ws.registry'] == pyramid_request.registry


def test_websocket_view_adds_work_queue_to_environ(pyramid_request):
    pyramid_request.get_response = lambda _: None

    views.websocket_view(pyramid_request)
    env = pyramid_request.environ

    assert env['h.ws.streamer_work_queue'] == streamer.WORK_QUEUE


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.registry.settings.update({'origins': []})
    # example.com is the dummy request default host URL
    pyramid_request.headers = {'Origin': 'http://example.com'}
    return pyramid_request
