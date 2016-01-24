import mock
import pytest

from h.sidebar import app_config


@pytest.mark.parametrize("url_in,url_out", [
    ("http://example.com", "ws://example.com"),
    ("https://example.com", "wss://example.com"),
    ("http://monkey.com:80/foo", "ws://monkey.com:80/foo"),
    ("https://giraffe.com:1443/ws?hello", "wss://giraffe.com:1443/ws?hello"),
])
def test_websocket_url(url_in, url_out):
    request = mock.Mock()

    def fake_route_url(url):
        if url == 'api':
            return 'https://hypothes.is/api'
        elif url == 'ws':
            return url_in

    request.route_url = fake_route_url
    result = app_config(request)

    assert result['websocketUrl'] == url_out
