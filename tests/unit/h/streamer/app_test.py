from unittest import mock

import pytest
from pyramid.config import Configurator

from h.sentry_filters import SENTRY_ERROR_FILTERS
from h.streamer.app import create_app


class TestIncludeMe:
    @pytest.mark.usefixtures("configure")
    def test_it_configures_pyramid_sentry_plugin(self, config, get_version):
        create_app(None)

        config.add_settings.assert_any_call(
            {
                "h_pyramid_sentry.filters": SENTRY_ERROR_FILTERS,
                "h_pyramid_sentry.celery_support": True,
                "h_pyramid_sentry.sqlalchemy_support": True,
                "h_pyramid_sentry.init.release": get_version.return_value,
                "h_pyramid_sentry.init.enable_logs": True,
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


@pytest.fixture(autouse=True)
def get_version(patch):
    return patch("h.streamer.app.get_version")
