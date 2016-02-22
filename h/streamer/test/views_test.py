# -*- coding: utf-8 -*-

import mock
from pyramid.testing import DummyRequest

from h.streamer import views


def test_websocket_view_bad_origin(config):
    config.registry.settings.update({'origins': 'http://good'})
    req = DummyRequest(headers={'Origin': 'http://bad'})
    res = views.websocket_view(req)
    assert res.code == 403


def test_websocket_view_good_origin(config):
    config.registry.settings.update({'origins': 'http://good'})
    req = DummyRequest(headers={'Origin': 'http://good'})
    req.get_response = lambda _: mock.sentinel.good_response
    res = views.websocket_view(req)
    assert res == mock.sentinel.good_response


def test_websocket_view_same_origin(config):
    # example.com is the dummy request default host URL
    req = DummyRequest(headers={'Origin': 'http://example.com'})
    req.get_response = lambda _: mock.sentinel.good_response
    res = views.websocket_view(req)
    assert res == mock.sentinel.good_response
