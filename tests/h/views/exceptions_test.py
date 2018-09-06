# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.views.exceptions import notfound, error, json_error


def test_notfound_view(pyramid_request):
    result = notfound(pyramid_request)

    assert pyramid_request.response.status_int == 404
    assert result == {}


def test_error_view(patch, pyramid_request):
    handle_exception = patch('h.views.exceptions.handle_exception')

    result = error(pyramid_request)

    handle_exception.assert_called_once_with(pyramid_request)
    assert result == {}


def test_json_error_view(patch, pyramid_request):
    handle_exception = patch('h.views.exceptions.handle_exception')

    result = json_error(pyramid_request)

    handle_exception.assert_called_once_with(pyramid_request)
    assert result['status'] == 'failure'
    assert result['reason']
