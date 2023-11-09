from unittest import mock

import pytest

from h.views.api import config as api_config


@pytest.mark.usefixtures("cors")
class TestAddApiView:
    def test_it_sets_default_accept_if_view_supports_default_version(
        self, pyramid_config, view
    ):
        api_config.add_api_view(
            pyramid_config, view, versions=["v1"], route_name="thing.read"
        )
        (_, kwargs) = pyramid_config.add_view.call_args_list[0]
        assert kwargs["accept"] == "application/json"

    def test_it_doesnt_set_default_accept_if_view_doesnt_support_default_version(
        self, pyramid_config, view
    ):
        api_config.add_api_view(
            pyramid_config, view, versions=["v2"], route_name="thing.read"
        )
        (_, kwargs) = pyramid_config.add_view.call_args_list[0]
        assert kwargs["accept"] != "application/json"

    def test_it_allows_accept_setting_override(self, pyramid_config, view):
        api_config.add_api_view(
            pyramid_config,
            view,
            versions=["v1"],
            accept="application/xml",
            route_name="thing.read",
        )
        (_, kwargs) = pyramid_config.add_view.call_args_list[0]
        assert kwargs["accept"] == "application/xml"

    def test_it_sets_renderer_setting(self, pyramid_config, view):
        api_config.add_api_view(
            pyramid_config, view, versions=["v1"], route_name="thing.read"
        )
        (_, kwargs) = pyramid_config.add_view.call_args_list[0]
        assert kwargs["renderer"] == "json"

    def test_it_allows_renderer_setting_override(self, pyramid_config, view):
        api_config.add_api_view(
            pyramid_config,
            view,
            versions=["v1"],
            route_name="thing.read",
            renderer="xml",
        )
        (_, kwargs) = pyramid_config.add_view.call_args_list[0]
        assert kwargs["renderer"] == "xml"

    def test_it_sets_default_decorators(
        self, pyramid_config, view, version_media_type_header
    ):
        api_config.add_api_view(
            pyramid_config, view, versions=["v1"], route_name="thing.read"
        )
        _, kwargs = pyramid_config.add_view.call_args_list[0]

        assert kwargs["decorator"] == (
            api_config.cors_policy,
            version_media_type_header("json"),
        )

    def test_it_adds_cors_preflight_view(self, pyramid_config, view, cors):
        api_config.add_api_view(
            pyramid_config, view, versions=["v1"], route_name="thing.read"
        )
        ([_, route_name, policy], _) = cors.add_preflight_view.call_args
        assert route_name == "thing.read"
        assert (
            policy == api_config.cors_policy  # pylint: disable=comparison-with-callable
        )

    def test_it_does_not_add_cors_preflight_view_if_disabled(
        self, pyramid_config, view, cors
    ):
        api_config.add_api_view(
            pyramid_config,
            view,
            versions=["v1"],
            route_name="thing.read",
            enable_preflight=False,
        )
        assert not cors.add_preflight_view.call_count

    def test_it_allows_decorator_override(self, pyramid_config, view):
        decorator = mock.Mock()
        api_config.add_api_view(
            pyramid_config,
            view,
            versions=["v1"],
            route_name="thing.read",
            decorator=decorator,
        )
        (_, kwargs) = pyramid_config.add_view.call_args
        assert kwargs["decorator"] == decorator

    def test_it_adds_default_version_accept(
        self, pyramid_config, view, media_type_for_version
    ):
        api_config.add_api_view(
            pyramid_config, view, versions=["v1"], route_name="thing.read"
        )
        (_, kwargs) = pyramid_config.add_view.call_args_list[1]

        media_type_for_version.assert_called_once_with("v1", subtype="json")
        assert kwargs["accept"] == media_type_for_version.return_value

    def test_it_raises_ValueError_on_unrecognized_version(self, pyramid_config, view):
        with pytest.raises(ValueError, match="Unrecognized API version"):
            api_config.add_api_view(
                pyramid_config, view, versions=["v3"], route_name="thing.read"
            )

    @pytest.mark.parametrize(
        "link_name,route_name,description,request_method",
        [
            ("read", "thing.read", "Fetch a thing", None),
            ("update", "thing.update", "Update a thing", ("PUT", "PATCH")),
            ("delete", "thing.delete", "Delete a thing", "DELETE"),
            (None, "thing.empty", None, None),
        ],
    )
    def test_it_adds_api_links_to_registry(
        self,
        pyramid_config,
        view,
        links,
        link_name,
        route_name,
        description,
        request_method,
    ):
        kwargs = {}
        if request_method:
            kwargs["request_method"] = request_method

        api_config.add_api_view(
            pyramid_config,
            view=view,
            versions=["v1"],
            link_name=link_name,
            description=description,
            route_name=route_name,
            **kwargs
        )

        if link_name:
            links.register_link.assert_called_once_with(
                link=links.ServiceLink(
                    name=link_name,
                    route_name=route_name,
                    method=request_method,
                    description=description,
                ),
                versions=["v1"],
                registry=pyramid_config.registry,
            )
        else:
            links.register_link.assert_not_called()

    @pytest.fixture
    def media_type_for_version(self, patch):
        return patch("h.views.api.config.media_type_for_version")

    @pytest.fixture
    def links(self, patch):
        return patch("h.views.api.config.links")

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

    @pytest.fixture
    def version_media_type_header(self, patch):
        return patch("h.views.api.config.version_media_type_header")
