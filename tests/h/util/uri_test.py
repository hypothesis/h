# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h._compat import text_type
from h.util import uri

TEST_URLS = [
    # Should replace http and https protocol with httpx
    ("https://example.org", "httpx://example.org"),
    ("http://example.org", "httpx://example.org"),
    # but not when scheme is not http or https
    ("ftp://example.org", "ftp://example.org"),
    ("file://example.org", "file://example.org"),


    # Should strip https://via.hypothes.is/ from the start of URIs
    ("https://via.hypothes.is/https://example.com", "httpx://example.com"),
    ("https://via.hypothes.is/http://foo.com/bar/", "httpx://foo.com/bar"),
    # but not when the URI isn't a proxied one
    ("https://via.hypothes.is", "httpx://via.hypothes.is"),
    ("https://via.hypothes.is/sample", "httpx://via.hypothes.is/sample"),

    # Should leave URNs as they are
    ("urn:doi:10.0001/12345", "urn:doi:10.0001/12345"),

    # Should leave http(s) URLs with no hostname as they are
    ("http:///path/to/page", "http:///path/to/page"),
    ("https:///path/to/page", "https:///path/to/page"),

    # Should treat messed up urlencoded strings as opaque and return them as
    # is. This is not valid urlencoding and trying to deal with it is going to
    # cause more problems than solutions (for example: is "%2F" in the path
    # section a path segment delimiter or a literal solidus?).
    ("http%3A%2F%2Fexample.com", "http%3A%2F%2Fexample.com"),
    ("http%3A%2F%2Fexample.com%2Ffoo%2F", "http%3A%2F%2Fexample.com%2Ffoo%2F"),

    # Should leave already-normalized URLs as they are
    ("http://example.com", "httpx://example.com"),
    ("https://foo.bar.org", "httpx://foo.bar.org"),

    # Should case-normalize scheme
    ("HtTp://example.com", "httpx://example.com"),
    ("HTTP://example.com", "httpx://example.com"),
    ("HtTpS://example.com", "httpx://example.com"),
    ("HTTPS://example.com", "httpx://example.com"),

    # Should case-normalize hostname
    ("http://EXAMPLE.COM", "httpx://example.com"),
    ("http://EXampLE.COM", "httpx://example.com"),

    # Should leave userinfo case alone
    ("http://Alice:p4SSword@example.com", "httpx://Alice:p4SSword@example.com"),
    ("http://BOB@example.com", "httpx://BOB@example.com"),

    # Should leave path case alone
    ("http://example.com/FooBar", "httpx://example.com/FooBar"),
    ("http://example.com/FOOBAR", "httpx://example.com/FOOBAR"),

    # Should strip URL fragments
    ("http://example.com#", "httpx://example.com"),
    ("http://example.com#bar", "httpx://example.com"),
    ("http://example.com/path#", "httpx://example.com/path"),
    ("http://example.com/path#!/hello/world", "httpx://example.com/path"),

    # Should remove default ports
    ("http://example.com:80", "httpx://example.com"),
    ("http://example.com:81", "httpx://example.com:81"),
    ("http://example.com:443", "httpx://example.com:443"),
    ("https://example.com:443", "httpx://example.com"),
    ("https://example.com:1443", "httpx://example.com:1443"),
    ("https://example.com:80", "httpx://example.com:80"),
    ("http://[fe80::3e15:c2ff:fed6:d198]:80", "httpx://[fe80::3e15:c2ff:fed6:d198]"),
    ("https://[fe80::3e15:c2ff:fed6:d198]:443", "httpx://[fe80::3e15:c2ff:fed6:d198]"),

    # Path: remove trailing slashes
    ("http://example.com/", "httpx://example.com"),
    ("http://example.com/////", "httpx://example.com"),
    ("http://example.com/foo/bar/baz/", "httpx://example.com/foo/bar/baz"),
    ("http://example.com/foo/bar/baz/////", "httpx://example.com/foo/bar/baz"),

    # Path: ensure UNRESERVED characters are decoded
    ("http://example.com/%7Ealice", "httpx://example.com/~alice"),
    ("http://example.com/~alice", "httpx://example.com/~alice"),
    ("http://example.com/goes%2Dto%2Dwonderland", "httpx://example.com/goes-to-wonderland"),
    ("http://example.com/goes-to-wonderland", "httpx://example.com/goes-to-wonderland"),
    ("http://example.com/%41%42%43/%31%32%33", "httpx://example.com/ABC/123"),
    ("http://example.com/hello%2Bworld", "httpx://example.com/hello+world"),
    ("http://example.com/hello+world", "httpx://example.com/hello+world"),
    ("http://example.com/%3A%40%2D%2E%5F%7E%21%24%26%27%28%29%2A%2B%2C%3D%3B",
     "httpx://example.com/:@-._~!$&'()*+,=;"),
    ("http://example.com/:@-._~!$&'()*+,=;", "httpx://example.com/:@-._~!$&'()*+,=;"),

    # Path: ensure RESERVED characters are encoded
    ("http://example.com/foo%2Fbar", "httpx://example.com/foo%2Fbar"),
    ("http://example.com/foo%3Fbar", "httpx://example.com/foo%3Fbar"),
    ("http://example.com/foo%5Bbar%5D", "httpx://example.com/foo%5Bbar%5D"),
    ("http://example.com/foo[bar]", "httpx://example.com/foo%5Bbar%5D"),

    # Path: ensure OTHER characters are encoded
    ("http://example.com/كذا", "httpx://example.com/%D9%83%D8%B0%D8%A7"),
    ("http://example.com/snowman/☃", "httpx://example.com/snowman/%E2%98%83"),

    # Path: normalize case of encodings
    ("http://example.com/case%2fnormalized", "httpx://example.com/case%2Fnormalized"),

    # Query: remove empty
    ("http://example.com?", "httpx://example.com"),

    # Query: Preserve the query string if we can't parse it
    ("http://example.com?&", "httpx://example.com?&"),
    ("http://example.com?foo=&", "httpx://example.com?foo=&"),

    # Query: ensure UNRESERVED characters are decoded
    ("http://example.com?foo%7Ebar=baz", "httpx://example.com?foo~bar=baz"),
    ("http://example.com?foo~bar=baz", "httpx://example.com?foo~bar=baz"),
    ("http://example.com?foo=bar%7Ebaz", "httpx://example.com?foo=bar~baz"),
    ("http://example.com?foo=bar~baz", "httpx://example.com?foo=bar~baz"),
    ("http://example.com?-._~:@!$'()*,=-._~:@!$='()*,",
     "httpx://example.com?-._~:@!$'()*,=-._~:@!$='()*,"),
    ("http://example.com?%2D%2E%5F%7E%3A%40%21%24%27%28%29%2A%2C=%2D%2E%5F%7E%3A%40%21%24%3D%27%28%29%2A%2C",
     "httpx://example.com?-._~:@!$'()*,=-._~:@!$='()*,"),

    # Query: ensure RESERVED characters are encoded
    ("http://example.com?foo bar=baz", "httpx://example.com?foo+bar=baz"),
    ("http://example.com?foo+bar=baz", "httpx://example.com?foo+bar=baz"),
    ("http://example.com?foo%20bar=baz", "httpx://example.com?foo+bar=baz"),
    ("http://example.com?foo=bar baz", "httpx://example.com?foo=bar+baz"),
    ("http://example.com?foo=bar+baz", "httpx://example.com?foo=bar+baz"),
    ("http://example.com?foo=bar%20baz", "httpx://example.com?foo=bar+baz"),
    ("http://example.com?foo%5Bbar%5D=baz", "httpx://example.com?foo%5Bbar%5D=baz"),
    ("http://example.com?foo[bar]=baz", "httpx://example.com?foo%5Bbar%5D=baz"),
    ("http://example.com?foo=%5Bbar%5Dbaz", "httpx://example.com?foo=%5Bbar%5Dbaz"),
    ("http://example.com?foo=[bar]baz", "httpx://example.com?foo=%5Bbar%5Dbaz"),

    # Query: ensure OTHER characters are encoded
    ("http://example.com?你好世界=γειά σου κόσμος",
     "httpx://example.com?%E4%BD%A0%E5%A5%BD%E4%B8%96%E7%95%8C=%CE%B3%CE%B5%CE%B9%CE%AC+%CF%83%CE%BF%CF%85+%CE%BA%CF%8C%CF%83%CE%BC%CE%BF%CF%82"),
    ("http://example.com?love=♥", "httpx://example.com?love=%E2%99%A5"),

    # Query: normalize case of encodings
    ("http://example.com?love=%e2%99%a5", "httpx://example.com?love=%E2%99%A5"),

    # Query: lexically sort parameters by name
    ("http://example.com?a=1&b=2", "httpx://example.com?a=1&b=2"),
    ("http://example.com?b=2&a=1", "httpx://example.com?a=1&b=2"),

    # Query: preserve relative ordering of multiple params with the same name
    ("http://example.com?b=2&b=3&b=1&a=1", "httpx://example.com?a=1&b=2&b=3&b=1"),
    ("http://example.com?b=&b=3&b=1&a=1", "httpx://example.com?a=1&b=&b=3&b=1"),

    # Query: remove parameters known to be irrelevant for document identity
    ("http://example.com?utm_source=abcde", "httpx://example.com"),
    ("http://example.com?utm_medium=abcde", "httpx://example.com"),
    ("http://example.com?utm_term=abcde", "httpx://example.com"),
    ("http://example.com?utm_content=abcde", "httpx://example.com"),
    ("http://example.com?utm_campaign=abcde", "httpx://example.com"),
    ("http://example.com?utm_source=abcde&utm_medium=wibble", "httpx://example.com"),
    ("http://example.com?a=1&utm_term=foo", "httpx://example.com?a=1"),
    ("http://example.com?a=1&utm_term=foo&b=2", "httpx://example.com?a=1&b=2"),
    ("http://example.com?WT.mc_id=TWT_NatureNews", "httpx://example.com"),
    ("http://example.com?WT.foo=bar", "httpx://example.com"),
    # but don't be over-eager and remove close matches
    ("http://example.com?gclid_foo=abcde", "httpx://example.com?gclid_foo=abcde"),
    ("http://example.com?bar_gclid=abcde", "httpx://example.com?bar_gclid=abcde"),
    ("http://example.com?WT=abcde", "httpx://example.com?WT=abcde"),
]


@pytest.mark.parametrize("url_in,url_out", TEST_URLS)
def test_normalize(url_in, url_out):
    assert uri.normalize(url_in) == url_out


@pytest.mark.parametrize("url,_", TEST_URLS)
def test_normalize_returns_unicode(url, _):
    assert isinstance(uri.normalize(url), text_type)
