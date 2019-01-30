# -*- coding: utf-8 -*-
"""Error tracking service API and setup."""
from __future__ import unicode_literals

import sentry_sdk
import sentry_sdk.integrations.celery
import sentry_sdk.integrations.pyramid

from h.sentry.helpers.before_send import before_send as _before_send


def report_exception(exc=None):
    """
    Report an exception to the error tracking service.

    If the given ``exc`` is :obj:`None` then the most recently raised exception
    will be reported.

    :arg exc: the exception to report
    :type exc: :class:`Exception`, :obj:`None`, or a :func:`sys.exc_info` tuple
    """
    sentry_sdk.capture_exception(exc)


def includeme(config):
    """Set up the error tracking service."""
    sentry_sdk.init(
        integrations=[
            sentry_sdk.integrations.celery.CeleryIntegration(),
            sentry_sdk.integrations.pyramid.PyramidIntegration(),
        ],
        environment=config.registry.settings["h.sentry_environment"],
        send_default_pii=True,
        before_send=_before_send,
    )
