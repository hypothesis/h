from unittest import mock
from unittest.mock import MagicMock

import pytest
from h_matchers import Any

from h import tweens
from h.util.redirects import Redirect


class TestRedirectTween:
    def test_it_loads_redirects(self, patch):
        parse_redirects = patch("h.tweens.parse_redirects")

        tweens.redirect_tween_factory(handler=None, registry=None)

        parse_redirects.assert_called_once_with(
            # Check parse_redirects is called with a file like object
            Any.object.with_attrs({"readlines": Any.callable()})
        )

    def test_it_loads_successfully(self):
        # Don't mock parse_redirects out to check the file actually parses
        tweens.redirect_tween_factory(handler=None, registry=None)

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

    def test_it_redirects_for_redirected_routes(self, pyramid_request):
        redirects = [
            Redirect(src="/foo", dst="http://bar", internal=False, prefix=False)
        ]

        pyramid_request.path = "/foo"

        tween = tweens.redirect_tween_factory(
            # pragma: nocover
            lambda req: req.response,
            pyramid_request.registry,
            redirects,
        )

        response = tween(pyramid_request)

        assert response.status_code == 301
        assert response.location == "http://bar"


class TestSecurityHeaderTween:
    def test_it_adds_security_headers_to_the_response(self, pyramid_request):
        tween = tweens.security_header_tween_factory(
            # pragma: nocover
            lambda req: req.response,
            pyramid_request.registry,
        )

        response = tween(pyramid_request)

        assert (
            response.headers["Referrer-Policy"]
            == "origin-when-cross-origin, strict-origin-when-cross-origin"
        )
        assert response.headers["X-XSS-Protection"] == "1; mode=block"


class TestCacheHeaderTween:
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


class TestDBRollbackSessionOnExceptionTween:
    def test_it_does_nothing_usually(self, handler, pyramid_request):
        tween = tweens.rollback_db_session_on_exception_factory(
            handler, pyramid_request.registry
        )

        tween(pyramid_request)

        handler.assert_called_once_with(pyramid_request)
        pyramid_request.db.rollback.assert_not_called()

    def test_it_calls_db_rollback_on_exception(self, handler, pyramid_request):
        handler.side_effect = IOError

        tween = tweens.rollback_db_session_on_exception_factory(
            handler, pyramid_request.registry
        )

        with pytest.raises(IOError):
            tween(pyramid_request)

        handler.assert_called_once_with(pyramid_request)
        pyramid_request.db.rollback.assert_called_once_with()

    @pytest.fixture
    def handler(self):
        return mock.create_autospec(lambda request: None)  # pragma: nocover

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.db = MagicMock(spec_set=["rollback"])
        return pyramid_request
