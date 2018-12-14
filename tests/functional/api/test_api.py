# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

# String type for request/response headers and metadata in WSGI.
#
# Per PEP-3333, this is intentionally `str` under both Python 2 and 3, even
# though it has different meanings.
#
# See https://www.python.org/dev/peps/pep-3333/#a-note-on-string-types
native_str = str


@pytest.mark.functional
class TestGetIndex(object):
    def test_api_index(self, app):
        """
        Test the API index view.

        This view is tested more thoroughly in the view tests, but this test
        checks the view doesn't error out and returns appropriate-looking JSON.
        """
        res = app.get("/api/")
        assert "links" in res.json


class TestCorsPreflight(object):
    def test_cors_preflight(self, app):
        # Simulate a CORS preflight request made by the browser from a client
        # hosted on a domain other than the one the service is running on.
        #
        # Note that no `Authorization` header is set.
        origin = "https://custom-client.herokuapp.com"
        headers = {
            "Access-Control-Request-Headers": str("authorization,content-type"),
            "Access-Control-Request-Method": str("POST"),
            "Origin": str(origin),
        }

        res = app.options("/api/annotations", headers=headers)

        assert res.status_code == 200
        assert res.headers["Access-Control-Allow-Origin"] == str(origin)
        assert "POST" in res.headers["Access-Control-Allow-Methods"]
        for header in ["Authorization", "Content-Type", "X-Client-Id"]:
            assert header in res.headers["Access-Control-Allow-Headers"]


class TestCorsHeaders(object):
    @pytest.mark.parametrize(
        "url, expect_errors",
        [
            # A request that succeeds.
            ("/api/search", False),
            # A request that triggers a validation error.
            ("/api/search?sort=raise_an_error", True),
            # A request that fails due to a missing resource.
            ("/api/annotations/does_not_exist", True),
        ],
    )
    def test_responses_have_cors_headers(self, app, url, expect_errors):
        res = app.get(url, expect_errors=expect_errors)
        assert res.headers.get("Access-Control-Allow-Origin", None) == "*"
