import pytest

from unittest.mock import MagicMock
from pyramid.testing import testConfig

from h_pyramid_sentry import includeme, report_exception
from h_pyramid_sentry.filters.pyramid import is_retryable_error


class TestReportException:
    def test_it_reports_the_exception_to_sentry(self, sentry_sdk):
        exc = ValueError("Test exception")

        report_exception(exc)

        sentry_sdk.capture_exception.assert_called_once_with(exc)

    def test_exc_defaults_to_none(self, sentry_sdk):
        report_exception()

        sentry_sdk.capture_exception.assert_called_once_with(None)


class TestIncludeMe:
    def test_it_initializes_sentry_sdk(self, pyramid_config, sentry_sdk, EventFilter):
        includeme(pyramid_config)

        sentry_sdk.init.assert_called_once_with(
            integrations=[
                sentry_sdk.integrations.celery.CeleryIntegration.return_value,
                sentry_sdk.integrations.pyramid.PyramidIntegration.return_value,
            ],
            environment="test",
            send_default_pii=True,
            before_send=EventFilter().before_send,
        )

    def test_it_reads_filter_configuration(self, pyramid_config, EventFilter):
        filter_functions = [lambda *args: 1]
        pyramid_config.registry.settings["h_pyramid_sentry.filters"] = filter_functions

        includeme(pyramid_config)

        EventFilter.assert_called_with(filter_functions)

    def test_it_reads_and_enables_retry_detection(self, pyramid_config, EventFilter):
        pyramid_config.registry.settings["h_pyramid_sentry.retry_support"] = True
        pyramid_config.scan = MagicMock()
        includeme(pyramid_config)

        EventFilter.assert_called_with([is_retryable_error])
        pyramid_config.scan.assert_called_with("h_pyramid_sentry.subscribers")

    @pytest.fixture
    def pyramid_config(self):
        with testConfig(settings={"h.sentry_environment": "test"}) as config:
            yield config

    @pytest.fixture
    def EventFilter(self, patch):
        return patch("h_pyramid_sentry.EventFilter")


@pytest.fixture(autouse=True)
def sentry_sdk(patch):
    return patch("h_pyramid_sentry.sentry_sdk")
