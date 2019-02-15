# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import mock
import pytest

from h.views.api import config as api_config


@pytest.mark.usefixtures("cors")
class TestAddApiView(object):
    def test_it_sets_accept_setting(self, pyramid_config, view):
        api_config.add_api_view(pyramid_config, view, route_name="thing.read")
        (_, kwargs) = pyramid_config.add_view.call_args
        assert kwargs["accept"] == "application/json"

    def test_it_allows_accept_setting_override(self, pyramid_config, view):
        api_config.add_api_view(
            pyramid_config, view, accept="application/xml", route_name="thing.read"
        )
        (_, kwargs) = pyramid_config.add_view.call_args
        assert kwargs["accept"] == "application/xml"

    def test_it_sets_renderer_setting(self, pyramid_config, view):
        api_config.add_api_view(pyramid_config, view, route_name="thing.read")
        (_, kwargs) = pyramid_config.add_view.call_args
        assert kwargs["renderer"] == "json"

    def test_it_allows_renderer_setting_override(self, pyramid_config, view):
        api_config.add_api_view(
            pyramid_config, view, route_name="thing.read", renderer="xml"
        )
        (_, kwargs) = pyramid_config.add_view.call_args
        assert kwargs["renderer"] == "xml"

    def test_it_sets_cors_decorator(self, pyramid_config, view):
        api_config.add_api_view(pyramid_config, view, route_name="thing.read")
        (_, kwargs) = pyramid_config.add_view.call_args
        assert kwargs["decorator"] == api_config.cors_policy

    def test_it_adds_cors_preflight_view(self, pyramid_config, view, cors):
        api_config.add_api_view(pyramid_config, view, route_name="thing.read")
        ([_, route_name, policy], _) = cors.add_preflight_view.call_args
        assert route_name == "thing.read"
        assert policy == api_config.cors_policy

    def test_it_does_not_add_cors_preflight_view_if_disabled(
        self, pyramid_config, view, cors
    ):
        api_config.add_api_view(
            pyramid_config, view, route_name="thing.read", enable_preflight=False
        )
        assert cors.add_preflight_view.call_count == 0

    def test_it_allows_decorator_override(self, pyramid_config, view):
        decorator = mock.Mock()
        api_config.add_api_view(
            pyramid_config, view, route_name="thing.read", decorator=decorator
        )
        (_, kwargs) = pyramid_config.add_view.call_args
        assert kwargs["decorator"] == decorator

    @pytest.mark.parametrize(
        "link_name,route_name,description,request_method,expected_method",
        [
            ("read", "thing.read", "Fetch a thing", None, "GET"),
            ("update", "thing.update", "Update a thing", ("PUT", "PATCH"), "PUT"),
            ("delete", "thing.delete", "Delete a thing", "DELETE", "DELETE"),
        ],
    )
    def test_it_adds_api_links_to_registry(
        self,
        pyramid_config,
        view,
        link_name,
        route_name,
        description,
        request_method,
        expected_method,
    ):
        kwargs = {}
        if request_method:
            kwargs["request_method"] = request_method

        api_config.add_api_view(
            pyramid_config,
            view=view,
            link_name=link_name,
            description=description,
            route_name=route_name,
            **kwargs
        )

        assert pyramid_config.registry.api_links == [
            {
                "name": link_name,
                "description": description,
                "method": expected_method,
                "route_name": route_name,
            }
        ]

    @pytest.fixture
    def pyramid_config(self, pyramid_config):
        pyramid_config.add_view = mock.Mock()
        return pyramid_config

    @pytest.fixture
    def cors(self, patch):
        return patch("h.views.api.config.cors")

    @pytest.fixture
    def view(self):
        return mock.Mock()
