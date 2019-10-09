import pytest

from pyramid.testing import testConfig

from h_pyramid_sentry import includeme, report_exception, EventFilter


class TestReportException:
    def test_it_reports_the_exception_to_sentry(self, sentry_sdk):
        exc = ValueError("Test exception")

        report_exception(exc)

        sentry_sdk.capture_exception.assert_called_once_with(exc)

    def test_exc_defaults_to_none(self, sentry_sdk):
        report_exception()

        sentry_sdk.capture_exception.assert_called_once_with(None)


class TestIncludeMe:
    def test_it_initializes_sentry_sdk(self, pyramid_config, sentry_sdk):
        includeme(pyramid_config)

        sentry_sdk.init.assert_called_once_with(
            integrations=[
                sentry_sdk.integrations.celery.CeleryIntegration.return_value,
                sentry_sdk.integrations.pyramid.PyramidIntegration.return_value,
            ],
            environment="test",
            send_default_pii=True,
            before_send=EventFilter.before_send,
        )

    @pytest.fixture
    def pyramid_config(self):
        with testConfig(settings={"h.sentry_environment": "test"}) as config:
            yield config


@pytest.fixture(autouse=True)
def sentry_sdk(patch):
    return patch("h_pyramid_sentry.sentry_sdk")
