# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from h import tweens
from h.util.redirects import Redirect


class TestRedirectTween(object):
    def test_it_loads_redirects(self, patch):
        open_ = patch("h.tweens.open")
        parse_redirects = patch("h.tweens.parse_redirects")

        tweens.redirect_tween_factory(handler=None, registry=None)

        open_.assert_called_once_with("h/redirects", encoding="utf-8")
        # Parse redirects is called with the value returned by the context manager
        parse_redirects.assert_called_once_with(
            open_.return_value.__enter__.return_value
        )

    def test_it_does_not_redirect_for_non_redirected_routes(self, pyramid_request):
        redirects = [
            Redirect(src="/foo", dst="http://bar", internal=False, prefix=False)
        ]

        pyramid_request.path = "/quux"

        tween = tweens.redirect_tween_factory(
            lambda req: req.response, pyramid_request.registry, redirects
        )

        response = tween(pyramid_request)

        assert response.status_code == 200

    def test_it_redirects_for_redirected_routes(self, pyramid_request, pyramid_config):
        redirects = [
            Redirect(src="/foo", dst="http://bar", internal=False, prefix=False)
        ]

        pyramid_request.path = "/foo"

        tween = tweens.redirect_tween_factory(
            lambda req: req.response, pyramid_request.registry, redirects
        )

        response = tween(pyramid_request)

        assert response.status_code == 301
        assert response.location == "http://bar"


class TestSecurityHeaderTween(object):
    def test_it_adds_security_headers_to_the_response(self, pyramid_request):
        tween = tweens.security_header_tween_factory(
            lambda req: req.response, pyramid_request.registry
        )

        response = tween(pyramid_request)

        assert (
            response.headers["Referrer-Policy"]
            == "origin-when-cross-origin, strict-origin-when-cross-origin"
        )
        assert response.headers["X-XSS-Protection"] == "1; mode=block"


class TestCacheHeaderTween(object):
    @pytest.mark.parametrize(
        "content_type, expected_cc_header",
        [
            # It doesn't add any headers for HTML pages.
            ("text/html", None),
            # It adds Cache-Control: no-cache for JSON responses.
            ("application/json", "no-cache"),
            # It doesn't add any headers for responses with no content (eg. 204
            # response to a `DELETE` request).
            (None, None),
        ],
    )
    def test_it_adds_caching_headers_to_the_response(
        self, pyramid_request, content_type, expected_cc_header
    ):
        tween = tweens.cache_header_tween_factory(
            lambda req: req.response, pyramid_request.registry
        )

        if content_type is not None:
            pyramid_request.response.headers["Content-Type"] = content_type

        response = tween(pyramid_request)

        assert response.headers.get("Cache-Control") == expected_cc_header


class TestEncodeHeadersTween(object):
    def test_it_converts_unicode_header_names_to_native_strings(
        self, pyramid_request, matchers, encode_headers_tween
    ):
        pyramid_request.response.headers["Access-Control-Allow-Origin"] = str("*")

        response = encode_headers_tween(pyramid_request)

        expected_header = matchers.NativeString("Access-Control-Allow-Origin")
        assert response.headers.getone(expected_header) == str("*")

    def test_it_converts_unicode_header_values_to_native_strings(
        self, pyramid_request, matchers, encode_headers_tween
    ):
        pyramid_request.response.headers[str("Access-Control-Allow-Origin")] = "*"

        response = encode_headers_tween(pyramid_request)

        expected_value = matchers.NativeString("*")
        assert (
            response.headers.getone(str("Access-Control-Allow-Origin"))
            == expected_value
        )

    def test_multiple_values_for_a_single_header(
        self, pyramid_request, matchers, encode_headers_tween
    ):
        pyramid_request.response.headers.add("foo", "bar")
        pyramid_request.response.headers.add(
            "foo", str("gar")
        )  # Already bytes in Python 2.
        pyramid_request.response.headers.add("foo", "zar")

        response = encode_headers_tween(pyramid_request)

        assert response.headers.getall(
            matchers.NativeString("foo")
        ) == matchers.UnorderedList(
            [
                matchers.NativeString("bar"),
                matchers.NativeString("gar"),
                matchers.NativeString("zar"),
            ]
        )

    @pytest.fixture
    def encode_headers_tween(self, pyramid_request):
        return tweens.encode_headers_tween_factory(
            lambda req: req.response, pyramid_request.registry
        )
