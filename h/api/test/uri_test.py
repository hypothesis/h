# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from mock import patch

from h.api import uri


@pytest.mark.parametrize("url_in,url_out", [
    # Should leave URNs as they are
    ("urn:doi:10.0001/12345", "urn:doi:10.0001/12345"),

    # Should treat messed up urlencoded strings as opaque and return them as
    # is. This is not valid urlencoding and trying to deal with it is going to
    # cause more problems than solutions (for example: is "%2F" in the path
    # section a path segment delimiter or a literal solidus?).
    ("http%3A%2F%2Fexample.com", "http%3A%2F%2Fexample.com"),
    ("http%3A%2F%2Fexample.com%2Ffoo%2F", "http%3A%2F%2Fexample.com%2Ffoo%2F"),

    # Should leave already-normalized URLs as they are
    ("http://example.com", "http://example.com"),
    ("https://foo.bar.org", "https://foo.bar.org"),

    # Should case-normalize scheme
    ("HtTp://example.com", "http://example.com"),
    ("HTTP://example.com", "http://example.com"),
    ("HtTpS://example.com", "https://example.com"),
    ("HTTPS://example.com", "https://example.com"),

    # Should case-normalize hostname
    ("http://EXAMPLE.COM", "http://example.com"),
    ("http://EXampLE.COM", "http://example.com"),

    # Should leave userinfo case alone
    ("http://Alice:p4SSword@example.com", "http://Alice:p4SSword@example.com"),
    ("http://BOB@example.com", "http://BOB@example.com"),

    # Should leave path case alone
    ("http://example.com/FooBar", "http://example.com/FooBar"),
    ("http://example.com/FOOBAR", "http://example.com/FOOBAR"),

    # Should strip URL fragments
    ("http://example.com#", "http://example.com"),
    ("http://example.com#bar", "http://example.com"),
    ("http://example.com/path#", "http://example.com/path"),
    ("http://example.com/path#!/hello/world", "http://example.com/path"),

    # Should remove default ports
    ("http://example.com:80", "http://example.com"),
    ("http://example.com:81", "http://example.com:81"),
    ("http://example.com:443", "http://example.com:443"),
    ("https://example.com:443", "https://example.com"),
    ("https://example.com:1443", "https://example.com:1443"),
    ("https://example.com:80", "https://example.com:80"),
    ("http://[fe80::3e15:c2ff:fed6:d198]:80", "http://[fe80::3e15:c2ff:fed6:d198]"),
    ("https://[fe80::3e15:c2ff:fed6:d198]:443", "https://[fe80::3e15:c2ff:fed6:d198]"),

    # Path: remove trailing slashes
    ("http://example.com/", "http://example.com"),
    ("http://example.com/////", "http://example.com"),
    ("http://example.com/foo/bar/baz/", "http://example.com/foo/bar/baz"),
    ("http://example.com/foo/bar/baz/////", "http://example.com/foo/bar/baz"),

    # Path: ensure UNRESERVED characters are decoded
    ("http://example.com/%7Ealice", "http://example.com/~alice"),
    ("http://example.com/~alice", "http://example.com/~alice"),
    ("http://example.com/goes%2Dto%2Dwonderland", "http://example.com/goes-to-wonderland"),
    ("http://example.com/goes-to-wonderland", "http://example.com/goes-to-wonderland"),
    ("http://example.com/%41%42%43/%31%32%33", "http://example.com/ABC/123"),
    ("http://example.com/hello%2Bworld", "http://example.com/hello+world"),
    ("http://example.com/hello+world", "http://example.com/hello+world"),
    ("http://example.com/%3A%40%2D%2E%5F%7E%21%24%26%27%28%29%2A%2B%2C%3D%3B", "http://example.com/:@-._~!$&'()*+,=;"),
    ("http://example.com/:@-._~!$&'()*+,=;", "http://example.com/:@-._~!$&'()*+,=;"),

    # Path: ensure RESERVED characters are encoded
    ("http://example.com/foo%2Fbar", "http://example.com/foo%2Fbar"),
    ("http://example.com/foo%3Fbar", "http://example.com/foo%3Fbar"),
    ("http://example.com/foo%5Bbar%5D", "http://example.com/foo%5Bbar%5D"),
    ("http://example.com/foo[bar]", "http://example.com/foo%5Bbar%5D"),

    # Path: ensure OTHER characters are encoded
    ("http://example.com/كذا", "http://example.com/%D9%83%D8%B0%D8%A7"),
    ("http://example.com/snowman/☃", "http://example.com/snowman/%E2%98%83"),

    # Path: normalize case of encodings
    ("http://example.com/case%2fnormalized", "http://example.com/case%2Fnormalized"),

    # Query: remove empty
    ("http://example.com?", "http://example.com"),

    # Query: ensure UNRESERVED characters are decoded
    ("http://example.com?foo%7Ebar=baz", "http://example.com?foo~bar=baz"),
    ("http://example.com?foo~bar=baz", "http://example.com?foo~bar=baz"),
    ("http://example.com?foo=bar%7Ebaz", "http://example.com?foo=bar~baz"),
    ("http://example.com?foo=bar~baz", "http://example.com?foo=bar~baz"),
    ("http://example.com?-._~:@!$'()*,=-._~:@!$='()*,", "http://example.com?-._~:@!$'()*,=-._~:@!$='()*,"),
    ("http://example.com?%2D%2E%5F%7E%3A%40%21%24%27%28%29%2A%2C=%2D%2E%5F%7E%3A%40%21%24%3D%27%28%29%2A%2C", "http://example.com?-._~:@!$'()*,=-._~:@!$='()*,"),

    # Query: ensure RESERVED characters are encoded
    ("http://example.com?foo bar=baz", "http://example.com?foo+bar=baz"),
    ("http://example.com?foo+bar=baz", "http://example.com?foo+bar=baz"),
    ("http://example.com?foo%20bar=baz", "http://example.com?foo+bar=baz"),
    ("http://example.com?foo=bar baz", "http://example.com?foo=bar+baz"),
    ("http://example.com?foo=bar+baz", "http://example.com?foo=bar+baz"),
    ("http://example.com?foo=bar%20baz", "http://example.com?foo=bar+baz"),
    ("http://example.com?foo%5Bbar%5D=baz", "http://example.com?foo%5Bbar%5D=baz"),
    ("http://example.com?foo[bar]=baz", "http://example.com?foo%5Bbar%5D=baz"),
    ("http://example.com?foo=%5Bbar%5Dbaz", "http://example.com?foo=%5Bbar%5Dbaz"),
    ("http://example.com?foo=[bar]baz", "http://example.com?foo=%5Bbar%5Dbaz"),

    # Query: ensure OTHER characters are encoded
    ("http://example.com?你好世界=γειά σου κόσμος", "http://example.com?%E4%BD%A0%E5%A5%BD%E4%B8%96%E7%95%8C=%CE%B3%CE%B5%CE%B9%CE%AC+%CF%83%CE%BF%CF%85+%CE%BA%CF%8C%CF%83%CE%BC%CE%BF%CF%82"),
    ("http://example.com?love=♥", "http://example.com?love=%E2%99%A5"),

    # Query: normalize case of encodings
    ("http://example.com?love=%e2%99%a5", "http://example.com?love=%E2%99%A5"),

    # Query: lexically sort parameters by name
    ("http://example.com?a=1&b=2", "http://example.com?a=1&b=2"),
    ("http://example.com?b=2&a=1", "http://example.com?a=1&b=2"),

    # Query: preserve relative ordering of multiple params with the same name
    ("http://example.com?b=2&b=3&b=1&a=1", "http://example.com?a=1&b=2&b=3&b=1"),
    ("http://example.com?b=&b=3&b=1&a=1", "http://example.com?a=1&b=&b=3&b=1"),

    # Query: remove parameters known to be irrelevant for document identity
    ("http://example.com?utm_source=abcde", "http://example.com"),
    ("http://example.com?utm_medium=abcde", "http://example.com"),
    ("http://example.com?utm_term=abcde", "http://example.com"),
    ("http://example.com?utm_content=abcde", "http://example.com"),
    ("http://example.com?utm_campaign=abcde", "http://example.com"),
    ("http://example.com?utm_source=abcde&utm_medium=wibble", "http://example.com"),
    ("http://example.com?a=1&utm_term=foo", "http://example.com?a=1"),
    ("http://example.com?a=1&utm_term=foo&b=2", "http://example.com?a=1&b=2"),
])
def test_normalize(url_in, url_out):
    assert uri.normalize(url_in) == url_out


def test_expand_no_document(document_model):
    document_model.get_by_uri.return_value = None
    assert uri.expand("http://example.com/") == ["http://example.com/"]


def test_expand_document_uris(document_model):
    document_model.get_by_uri.return_value.uris.return_value = [
        "http://foo.com/",
        "http://bar.com/",
    ]
    assert uri.expand("http://example.com/") == [
        "http://foo.com/",
        "http://bar.com/",
    ]


@pytest.fixture
def document_model(config, request):
    patcher = patch('h.api.models.Document', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
