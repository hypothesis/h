# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.exceptions import APIError
from h.views.api_exceptions import api_notfound, api_error, json_error


def test_api_notfound_view(pyramid_request):
    result = api_notfound(pyramid_request)

    assert pyramid_request.response.status_int == 404
    assert result['status'] == 'failure'
    assert result['reason']


def test_api_error_view(pyramid_request):
    context = APIError(message='asplosions!', status_code=418)

    result = api_error(context, pyramid_request)

    assert pyramid_request.response.status_code == 418
    assert result['status'] == 'failure'
    assert result['reason'] == 'asplosions!'


def test_json_error_view(patch, pyramid_request):
    handle_exception = patch('h.views.api_exceptions.handle_exception')

    result = json_error(pyramid_request)

    handle_exception.assert_called_once_with(pyramid_request)
    assert result['status'] == 'failure'
    assert result['reason']
