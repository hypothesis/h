"""Error tracking service API and setup."""
import sentry_sdk
import sentry_sdk.integrations.celery
import sentry_sdk.integrations.pyramid

from h_pyramid_sentry.event_filter import EventFilter


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
    filters = [
        # Allow functions to be passed as strings: e.g. "module.function"
        config.maybe_dotted(_filter)
        for _filter in config.registry.settings.get("h_pyramid_sentry.filters", [])
    ]

    if config.registry.settings.get("h_pyramid_sentry.retry_support"):
        from h_pyramid_sentry.filters.pyramid import is_retryable_error

        filters.append(is_retryable_error)
        config.scan("h_pyramid_sentry.subscribers")

    event_filter = EventFilter(filters)

    sentry_sdk.init(
        integrations=[
            # This looks a bit goofy, but makes mocking in the tests easier
            # as you only have to mock the sentry_sdk package
            sentry_sdk.integrations.celery.CeleryIntegration(),
            sentry_sdk.integrations.pyramid.PyramidIntegration(),
        ],
        environment=config.registry.settings["h.sentry_environment"],
        send_default_pii=True,
        before_send=event_filter.before_send,
    )
