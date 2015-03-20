"""Unit tests for h/api_client/api_client.py."""
import mock
import pytest
import requests.exceptions

from h import api_client


@mock.patch("requests.get")
def test_get(mock_get):
    """get() should request the right URL."""
    def mock_get_function(url, params, timeout):
        assert url == "http://www.example.com/api/stream"
        assert params is None
        return mock.Mock()

    mock_get.side_effect = mock_get_function

    client = api_client.Client("http://www.example.com/api")
    client.get("/stream")

    assert mock_get.call_count == 1


@mock.patch("requests.get")
def test_get_with_trailing_slash_on_root_url(mock_get):
    """get() should handle base URLs with trailing /'s correctly."""
    def mock_get_function(url, params, timeout):
        assert url == "http://www.example.com/api/stream"
        assert params is None
        return mock.Mock()

    mock_get.side_effect = mock_get_function

    # Trailing slash.
    client = api_client.Client("http://www.example.com/api/")

    client.get("/stream")

    assert mock_get.call_count == 1


@mock.patch("requests.get")
def test_get_without_leading_slash_on_path(mock_get):
    """get() should handle paths with no leading slash.

    Even when the root_url doesn't have a trailing slash.

    """
    def mock_get_function(url, params, timeout):
        assert url == "http://www.example.com/api/stream"
        assert params is None
        return mock.Mock()

    mock_get.side_effect = mock_get_function

    # No trailing slash.
    client = api_client.Client("http://www.example.com/api")
    client.get("stream")  # No leading slash.

    assert mock_get.call_count == 1


@mock.patch("requests.get")
def test_get_with_url_params(mock_get):
    """get() should pass the right URL params to requests.get()."""
    def mock_get_function(url, params, timeout):
        assert params == {"limit": 10, "foo": "bar"}
        return mock.Mock()

    mock_get.side_effect = mock_get_function

    client = api_client.Client("http://www.example.com/api")
    client.get("/stream", params={"limit": 10, "foo": "bar"})

    assert mock_get.call_count == 1


@mock.patch("requests.get")
def test_connection_error(mock_get):
    """get() should raise ConnectionError if requests.get() does."""
    mock_get.side_effect = requests.exceptions.ConnectionError
    client = api_client.Client("http://www.example.com/api")

    with pytest.raises(api_client.ConnectionError):
        client.get("/stream")


@mock.patch("requests.get")
def test_timeout(mock_get):
    """get() should raise Timeout if requests.get() does."""
    mock_get.side_effect = requests.exceptions.Timeout
    client = api_client.Client("http://www.example.com/api")

    with pytest.raises(api_client.Timeout):
        client.get("/stream")


@mock.patch("requests.get")
def test_unknown_exception(mock_get):
    """get() should raise APIError if requests raises an unknown exception."""
    mock_get.side_effect = requests.exceptions.ChunkedEncodingError
    client = api_client.Client("http://www.example.com/api")

    with pytest.raises(api_client.APIError):
        client.get("/stream")


def test_invalid_base_url():
    """get() should raise APIError if given an invalid base_url."""
    client = api_client.Client("invalid")

    with pytest.raises(api_client.APIError):
        client.get("/stream")
