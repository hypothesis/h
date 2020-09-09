import pytest


class TestCorsPreflight:
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


class TestCorsHeaders:
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
