from unittest import mock

import pytest
from pyramid.config import Configurator

from h.sentry_filters import SENTRY_FILTERS
from h.streamer.app import create_app


class TestIncludeMe:
    @pytest.mark.usefixtures("configure")
    def test_it_configures_pyramid_sentry_plugin(self, config):
        create_app(None)

        config.add_settings.assert_any_call(
            {
                "h_pyramid_sentry.filters": SENTRY_FILTERS,
                "h_pyramid_sentry.celery_support": True,
            }
        )

    @pytest.fixture
    def config(self):
        return mock.create_autospec(Configurator, instance=True)

    @pytest.fixture
    def configure(self, patch, config):
        configure = patch("h.streamer.app.configure")
        configure.return_value = config

        return configure
