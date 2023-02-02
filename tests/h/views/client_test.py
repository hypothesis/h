import json

import pytest
from pyramid.httpexceptions import HTTPFound

from h.views import client


@pytest.mark.usefixtures("routes", "pyramid_settings")
class TestSidebarApp:
    def test_it_includes_client_config(self, pyramid_request):
        ctx = client.sidebar_app(pyramid_request)
        expected_config = {
            "apiUrl": "http://example.com/api",
            "sentry": {"dsn": "test-sentry-dsn", "environment": "dev"},
            "authDomain": "example.com",
            "oauthClientId": "test-client-id",
            "rpcAllowedOrigins": "https://lti.hypothes.is",
        }

        actual_config = json.loads(ctx["app_config"])

        assert actual_config == expected_config

    def test_it_sets_client_url(self, pyramid_request):
        ctx = client.sidebar_app(pyramid_request)

        assert ctx["client_url"] == "http://example.com/client_url"

    def test_it_sets_custom_content_security_policy_header(self, pyramid_request):
        client.sidebar_app(pyramid_request)
        csp_header = pyramid_request.response.headers["Content-Security-Policy"]

        assert (
            csp_header
            == "script-src http://example.com; style-src http://example.com 'unsafe-inline'"
        )


@pytest.mark.usefixtures("routes", "pyramid_settings")
class TestEmbedRedirect:
    def test_redirects_to_client_boot_script(self, pyramid_request):
        rsp = client.embed_redirect(pyramid_request)

        assert isinstance(rsp, HTTPFound)
        assert rsp.location == "http://example.com/client_url"

    def test_adds_cachebuster(self, pyramid_request):
        pyramid_request.feature.flags["embed_cachebuster"] = True

        rsp = client.embed_redirect(pyramid_request)

        assert isinstance(rsp, HTTPFound)
        assert "?cachebuster=" in rsp.location


@pytest.fixture
def pyramid_settings(pyramid_settings):
    pyramid_settings.update(
        {
            "h.client_oauth_id": "test-client-id",
            "h.sentry_dsn_client": "test-sentry-dsn",
            "h.sentry_environment": "dev",
            "h.websocket_url": "wss://example.com/ws",
            "h.client_rpc_allowed_origins": "https://lti.hypothes.is",
            "h.client_url": "{current_scheme}://{current_host}/client_url",
            "authority": "example.com",
        }
    )

    return pyramid_settings


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.feature.flags["embed_cachebuster"] = False
    return pyramid_request


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("api.index", "/api")
    pyramid_config.add_route("embed", "/embed.js")
    pyramid_config.add_route("index", "/")
    pyramid_config.add_route("sidebar_app", "/app.html")
    pyramid_config.add_route("oauth_authorize", "/oauth/authorize")
    pyramid_config.add_route("oauth_revoke", "/oauth/revoke")
