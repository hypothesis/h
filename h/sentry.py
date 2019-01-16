# -*- coding: utf-8 -*-
"""Error tracking service API and setup."""
from __future__ import unicode_literals

import sentry_sdk
import sentry_sdk.integrations.celery
import sentry_sdk.integrations.pyramid


def _before_send(event, hint):
    logger = event.get("logger")
    message = event.get("logentry", {}).get("message")

    # Filter out ws4py's "Error when terminating connection" message. It logs
    # thousands of these a day in production and I don't think they're
    # actually a problem.
    # See: https://github.com/hypothesis/h/issues/5496
    if logger == "ws4py" and message.startswith(
        "Error when terminating the connection"
    ):
        return None

    return event


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
