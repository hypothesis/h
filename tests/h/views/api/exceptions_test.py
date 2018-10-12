# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import Mock

from h.exceptions import APIError
from h.schemas import ValidationError
from h.views.api import exceptions as views


def test_api_notfound_view(pyramid_request):
    result = views.api_notfound(pyramid_request)

    assert pyramid_request.response.status_int == 404
    assert result['status'] == 'failure'
    assert result['reason']


def test_api_error_view(pyramid_request):
    context = APIError(message='asplosions!', status_code=418)

    result = views.api_error(context, pyramid_request)

    assert pyramid_request.response.status_code == 418
    assert result['status'] == 'failure'
    assert result['reason'] == 'asplosions!'


def test_api_validation_error(pyramid_request):
    context = ValidationError('missing required userid')

    result = views.api_validation_error(context, pyramid_request)

    assert pyramid_request.response.status_code == 400
    assert result['status'] == 'failure'
    assert result['reason'] == 'missing required userid'


def test_json_error_view(patch, pyramid_request):
    handle_exception = patch('h.views.api.exceptions.handle_exception')

    exception = Mock()
    result = views.json_error(exception, pyramid_request)

    handle_exception.assert_called_once_with(pyramid_request, exception)
    assert result['status'] == 'failure'
    assert result['reason']
