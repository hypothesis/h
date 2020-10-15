from unittest import mock

import pytest
from pyramid.config import Configurator

from h.sentry_filters import SENTRY_FILTERS
from h.streamer.app import create_app


class TestIncludeMe:
    def test_it_configures_pyramid_sentry_plugin(self, configure, config):
        create_app(None)

        config.add_settings.assert_any_call(
            {
                "h_pyramid_sentry.filters": SENTRY_FILTERS,
                "h_pyramid_sentry.celery_support": True,
            }
        )

    @pytest.mark.usefixtures("with_kill_switch_on")
    def test_it_respects_the_kill_switch(self, configure, config):
        create_app(None)

        config.add_settings.assert_not_called()
        config.add_tween.assert_not_called()
        config.set_authentication_policy.assert_not_called()
        config.add_route.assert_not_called()

        config.scan.assert_called_once_with("h.streamer.kill_switch_views")

    @pytest.fixture
    def with_kill_switch_on(self, patch):
        os = patch("h.streamer.app.os")
        os.environ.get.side_effect = {"KILL_SWITCH_WEBSOCKET": 1}.get

    @pytest.fixture
    def config(self):
        return mock.create_autospec(Configurator, instance=True)

    @pytest.fixture
    def configure(self, patch, config):
        configure = patch("h.streamer.app.configure")
        configure.return_value = config

        return configure
