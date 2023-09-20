import pytest

from h.search import util

pytestmark = [
    pytest.mark.xdist_group("elasticsearch"),
    pytest.mark.usefixtures("init_elasticsearch"),
]


@pytest.mark.parametrize(
    "wildcard_uri,expected",
    [
        ("htt*://bar.com", False),
        ("*http://bar.com", False),
        ("http_://bar.com", False),
        ("http://bar_com*", False),
        ("_http://bar.com", False),
        ("http://localhost:3000*", False),
        ("http://localhost:_3000", False),
        ("http://bar.com_foo=baz", False),
        ("http://example.com_", False),
        ("http://bar*.com", False),
        ("file://*", False),
        ("https://foo.com", False),
        ("http://foo.com*", False),
        ("http://foo.com/*", True),
        ("urn:*", True),
        ("doi:10.101_", True),
        ("http://example.com/__/", True),
    ],
)
def test_identifies_wildcard_uri_is_valid(wildcard_uri, expected):
    assert util.wildcard_uri_is_valid(wildcard_uri) == expected


@pytest.mark.parametrize(
    "uri,expected",
    [
        ("htt*://bar.com", "htt*://bar.com"),
        ("*bar.com", "http://*bar.com"),
        ("*http://bar.com", "*http://bar.com"),
        ("http_://bar.com", "http_://bar.com"),
        ("http://bar_com*", "http://bar_com*"),
        ("server:9000", "server:9000"),
        ("http://localhost:3000*", "http://localhost:3000*"),
        ("file://*", "file://*"),
        ("urn:*", "urn:*"),
        ("doi:10.101_", "doi:10.101_"),
    ],
)
def test_add_default_scheme(uri, expected):
    assert util.add_default_scheme(uri) == expected
