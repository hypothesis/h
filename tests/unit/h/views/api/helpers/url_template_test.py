import pytest

from h.views.api.helpers.url_template import RouteNotFoundError, route_url_template


class TestRouteURLTemplate:
    @pytest.mark.parametrize(
        "route_name,expected",
        [
            # No params
            ("folders", "http://example.com/folders"),
            # One param
            ("folders.list", "http://example.com/folders/:folderid"),
            # Multiple params
            ("file.read", "http://example.com/folders/:folderid/files/:fileid"),
            # Complex patterns
            ("folders.list.v2", "http://example.com/folders/:folderid"),
        ],
    )
    def test_it(self, pyramid_request, route_name, expected):
        assert route_url_template(pyramid_request, route_name) == expected

    def test_it_raises_if_route_not_found(self, pyramid_request):
        with pytest.raises(RouteNotFoundError) as exc_info:
            route_url_template(pyramid_request, "invalid.route")
        assert exc_info.value.route_name == "invalid.route"

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("folders", "/folders")
        pyramid_config.add_route("folders.list", "/folders/{folderid}")
        pyramid_config.add_route("file.read", "/folders/{folderid}/files/{fileid}")
        pyramid_config.add_route("folders.list.v2", "/folders/{folderid:[0-9]{5}}")
