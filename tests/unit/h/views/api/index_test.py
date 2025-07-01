import pytest
from h_matchers import Any
from pyramid.config import Configurator

from h.views.api import index as views


class TestIndex:
    def test_it_returns_links(self, pyramid_request):
        result = views.index(None, pyramid_request)

        assert "links" in result

    def test_it_returns_links_for_the_right_version(
        self, pyramid_request, link_helpers, route_url_template
    ):
        views.index(None, pyramid_request)

        link_helpers.format_nested_links.assert_called_once_with(
            pyramid_request.registry.api_links["v1"], Any.function()
        )
        route_url = link_helpers.format_nested_links.call_args[0][1]
        route_url("a.route")
        route_url_template.assert_called_with(pyramid_request, "a.route")


class TestIndexV2:
    def test_it_returns_links(self, pyramid_request):
        result = views.index_v2(None, pyramid_request)

        assert "links" in result

    def test_it_returns_links_for_the_right_version(
        self, pyramid_request, link_helpers, route_url_template
    ):
        views.index_v2(None, pyramid_request)

        link_helpers.format_nested_links.assert_called_once_with(
            pyramid_request.registry.api_links["v2"], Any.function()
        )
        route_url = link_helpers.format_nested_links.call_args[0][1]
        route_url("a.route")
        route_url_template.assert_called_with(pyramid_request, "a.route")


@pytest.fixture
def pyramid_request(pyramid_config, pyramid_request):
    # Scan `h.views.api_annotations` for API link metadata specified in @api_config
    # declarations.
    config = Configurator()
    config.scan("h.views.api.annotations")
    config.scan("h.views.api.index")
    # Any route referenced in `h.views.api.annotations` needs to be added here
    pyramid_config.add_route("api.search", "/dummy/search")
    pyramid_config.add_route("api.annotations", "/dummy/annotations")
    pyramid_config.add_route("api.annotation", "/dummy/annotations/:id")
    pyramid_request.registry.api_links = config.registry.api_links

    return pyramid_request


@pytest.fixture
def link_helpers(patch):
    return patch("h.views.api.index.link_helpers")


@pytest.fixture(autouse=True)
def route_url_template(patch):
    return patch("h.views.api.index.route_url_template")
