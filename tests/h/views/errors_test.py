from unittest.mock import Mock

from h.views.errors import error, json_error, notfound


def test_notfound_view(pyramid_request):
    result = notfound(pyramid_request)

    assert pyramid_request.response.status_int == 404
    assert not result


def test_error_view(patch, pyramid_request):
    handle_exception = patch("h.views.errors.handle_exception")
    exception = Mock()

    result = error(exception, pyramid_request)

    handle_exception.assert_called_once_with(pyramid_request, exception)
    assert not result


def test_json_error_view(patch, pyramid_request):
    handle_exception = patch("h.views.errors.handle_exception")
    exception = Mock()

    result = json_error(exception, pyramid_request)

    handle_exception.assert_called_once_with(pyramid_request, exception)
    assert result["status"] == "failure"
    assert result["reason"]
