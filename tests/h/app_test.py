from unittest import mock

import pytest
from pyramid_jinja2 import Environment as JinjaEnvironment

from h.app import includeme
from h.assets import Environment
from h.sentry_filters import SENTRY_FILTERS


class TestIncludeMe:
    def test_it_configures_pyramid_sentry_plugin(self, pyramid_config):
        includeme(pyramid_config)

        settings = pyramid_config.registry.settings

        assert settings["h_pyramid_sentry.retry_support"] is True
        assert settings["h_pyramid_sentry.celery_support"] is True
        assert settings["h_pyramid_sentry.filters"] == SENTRY_FILTERS

        pyramid_config.include.assert_any_call("h_pyramid_sentry")

    @pytest.fixture
    def pyramid_config(self, pyramid_config):
        # Mock out jinja2 related stuff
        pyramid_config.get_jinja2_environment = mock.create_autospec(
            spec=lambda: JinjaEnvironment()  # pylint: disable=unnecessary-lambda
        )

        pyramid_config.registry["assets_env"] = Environment(
            assets_base_url=mock.sentinel.assets_base_url,
            bundle_config_path=mock.sentinel.bundle_config_path,
            manifest_path=mock.sentinel.manifest_path,
            auto_reload=True,
        )

        pyramid_config.add_jinja2_extension = mock.create_autospec(lambda name: True)

        # Prevent us from really loading the includes
        pyramid_config.include = mock.create_autospec(lambda name: True)

        return pyramid_config
