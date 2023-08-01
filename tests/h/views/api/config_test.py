from unittest.mock import call, patch, sentinel

import pytest
from h_matchers import Any

from h.views.api.config import _add_api_view, cors_policy


class TestAddAPIView:
    @pytest.mark.parametrize("subtype", ("json", "ndjson"))
    @pytest.mark.parametrize("enable_preflight", (True, False))
    def test_it(
        self,
        pyramid_config,
        version_media_type_header,
        cors,
        links,
        subtype,
        enable_preflight,
    ):
        # These items are all passed through verbatim to `add_view`
        settings = {
            "any_extra": sentinel.any_extra,
            "request_method": sentinel.request_method,
            "route_name": sentinel.route_name,
        }

        _add_api_view(
            config=pyramid_config,
            view=sentinel.view,
            versions=["v2"],
            link_name=sentinel.link_name,
            description=sentinel.description,
            enable_preflight=enable_preflight,
            subtype=subtype,
            **settings,
        )

        links.ServiceLink.assert_called_once_with(
            name=sentinel.link_name,
            route_name=sentinel.route_name,
            method=sentinel.request_method,
            description=sentinel.description,
        )
        links.register_link.assert_called_once_with(
            links.ServiceLink.return_value, ["v2"], pyramid_config.registry
        )
        version_media_type_header.assert_called_once_with(subtype)
        pyramid_config.add_view.assert_called_once_with(
            view=sentinel.view,
            renderer="json",
            decorator=(cors_policy, version_media_type_header.return_value),
            accept=f"application/vnd.hypothesis.v2+{subtype}",
            **settings,
        )
        if enable_preflight:
            cors.add_preflight_view.assert_called_once_with(
                pyramid_config, sentinel.route_name, cors_policy
            )
        else:
            cors.add_preflight_view.assert_not_called()

    def test_it_with_minimal_args(
        self, pyramid_config, version_media_type_header, cors, links
    ):
        _add_api_view(
            config=pyramid_config,
            view=sentinel.view,
            versions=["v2"],
            enable_preflight=False,
        )

        links.register_link.assert_not_called()
        version_media_type_header.assert_called_once_with("json")
        pyramid_config.add_view.assert_called_once_with(
            view=Any(),
            renderer=Any(),
            decorator=Any(),
            accept="application/vnd.hypothesis.v2+json",
        )
        cors.add_preflight_view.assert_not_called()

    @pytest.mark.parametrize("subtype", ("json", "ndjson"))
    def test_it_with_v1(self, pyramid_config, version_media_type_header, subtype):
        _add_api_view(
            config=pyramid_config,
            view=sentinel.view,
            versions=["v1"],
            enable_preflight=False,
            subtype=subtype,
        )

        shared_view_settings = {
            "view": sentinel.view,
            "renderer": "json",
            "decorator": (cors_policy, version_media_type_header.return_value),
        }
        pyramid_config.add_view.assert_has_calls(
            [
                call(**shared_view_settings, accept="application/json"),
                call(
                    **shared_view_settings,
                    accept=f"application/vnd.hypothesis.v1+{subtype}",
                ),
            ]
        )

    def test_it_fails_with_unexpected_version_numbers(self, pyramid_config):
        with pytest.raises(ValueError):
            _add_api_view(
                config=pyramid_config, view=sentinel.view, versions=["v99999"]
            )

    @pytest.fixture
    def cors(self, patch):
        return patch("h.views.api.config.cors")

    @pytest.fixture
    def links(self, patch):
        return patch("h.views.api.config.links")

    @pytest.fixture
    def version_media_type_header(self, patch):
        return patch("h.views.api.config.version_media_type_header")

    @pytest.fixture(autouse=True)
    def add_view(self, pyramid_config):
        with patch.object(pyramid_config, "add_view") as add_view:
            yield add_view
