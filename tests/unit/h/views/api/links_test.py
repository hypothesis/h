from pyramid import testing

from h.views.api import links as views


class TestLinks:
    def test_it_returns_the_right_links(self, pyramid_config, pyramid_request):
        pyramid_config.add_route("account", "/account/settings")
        pyramid_config.add_route("forgot_password", "/forgot-password")
        pyramid_config.add_route("group_create", "/groups/new")
        pyramid_config.add_route("help", "/docs/help")
        pyramid_config.add_route("oauth_authorize", "/oauth/authorize")
        pyramid_config.add_route("oauth_revoke", "/oauth/revoke")
        pyramid_config.add_route("activity.search", "/search")
        pyramid_config.add_route("signup", "/signup")
        pyramid_config.add_route("stream.user_query", "/u/{user}")
        pyramid_request.registry.settings["h.websocket_url"] = "wss://example.com/ws"

        links = views.links(testing.DummyResource(), pyramid_request)

        host = "http://example.com"  # Pyramid's default host URL.
        assert links == {
            "account.settings": host + "/account/settings",
            "forgot-password": host + "/forgot-password",
            "groups.new": host + "/groups/new",
            "help": host + "/docs/help",
            "oauth.authorize": host + "/oauth/authorize",
            "oauth.revoke": host + "/oauth/revoke",
            "search.tag": host + "/search?q=tag%3A%22:tag%22",
            "signup": host + "/signup",
            "user": host + "/u/:user",
            "websocket": "wss://example.com/ws",
        }
