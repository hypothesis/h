from unittest.mock import Mock

from pyramid.httpexceptions import HTTPExpectationFailed, HTTPNotFound

from h.views.api import errors as views


def test_api_notfound_view(pyramid_request):
    result = views.api_notfound(HTTPNotFound("Some Reason"), pyramid_request)

    assert pyramid_request.response.status_int == 404
    assert result["status"] == "failure"
    assert result["reason"]


def test_api_error_view(pyramid_request):
    context = HTTPExpectationFailed(detail="asplosions!")

    result = views.api_error(context, pyramid_request)

    assert pyramid_request.response.status_code == 417
    assert result["status"] == "failure"
    assert result["reason"] == "asplosions!"


def test_json_error_view(patch, pyramid_request):
    handle_exception = patch("h.views.api.errors.handle_exception")

    exception = Mock()
    result = views.json_error(exception, pyramid_request)

    handle_exception.assert_called_once_with(pyramid_request, exception)
    assert result["status"] == "failure"
    assert result["reason"]
