# -*- coding: utf-8 -*-

import pytest

from h import jinja_extensions as ext


@pytest.mark.parametrize("url_in,url_out", [
    ("http://example.com", "ws://example.com"),
    ("https://example.com", "wss://example.com"),
    ("http://monkey.com:80/foo", "ws://monkey.com:80/foo"),
    ("https://giraffe.com:1443/ws?hello", "wss://giraffe.com:1443/ws?hello"),
])
def test_websocketize(url_in, url_out):
    result = ext.websocketize(url_in)

    assert result == url_out


@pytest.mark.parametrize("url", [
    "foo",
    "ftp://wat/",
    "ws://example.com",
])
def test_websocketize_raises_on_non_http_https_urls(url):
    with pytest.raises(ValueError):
        ext.websocketize(url)
