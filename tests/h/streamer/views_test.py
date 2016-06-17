# -*- coding: utf-8 -*-

import mock

from h.streamer import views


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
    # example.com is the dummy request default host URL
    pyramid_request.registry.settings.update({'origins': []})
    pyramid_request.headers = {'Origin': 'http://example.com'}
    pyramid_request.get_response = lambda _: mock.sentinel.good_response
    res = views.websocket_view(pyramid_request)
    assert res == mock.sentinel.good_response
