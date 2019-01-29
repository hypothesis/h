# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from h.sentry import includeme, report_exception
from h.sentry.helpers.before_send import before_send


class TestReportException(object):
    def test_it_reports_the_exception_to_Sentry(self, sentry_sdk):
        exc = ValueError("Test exception")

        report_exception(exc)

        sentry_sdk.capture_exception.assert_called_once_with(exc)

    def test_exc_defaults_to_None(self, sentry_sdk):
        report_exception()

        sentry_sdk.capture_exception.assert_called_once_with(None)


class TestIncludeMe(object):
    def test_it_initializes_sentry_sdk(self, pyramid_config, sentry_sdk):
        includeme(pyramid_config)

        sentry_sdk.init.assert_called_once_with(
            integrations=[
                sentry_sdk.integrations.celery.CeleryIntegration.return_value,
                sentry_sdk.integrations.pyramid.PyramidIntegration.return_value,
            ],
            environment="test",
            send_default_pii=True,
            before_send=before_send,
        )

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config):
        pyramid_config.registry.settings["h.sentry_environment"] = "test"
        return pyramid_config


@pytest.fixture(autouse=True)
def sentry_sdk(patch):
    return patch("h.sentry.sentry_sdk")
