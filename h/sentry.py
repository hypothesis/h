import logging


def configure_sentry_logger(dsn):
    """
    Configure the Sentry log handler for the provided DSN.
    """
    # Import raven modules at runtime because this is an optional module. This
    # function will only be called if the 'sentry.dsn' setting is provided.
    # pylint: disable=import-error
    from raven.conf import setup_logging
    from raven.handlers.logging import SentryHandler
    # pylint: enable=import-error

    handler = SentryHandler(dsn, level=logging.WARN)
    setup_logging(handler)


def includeme(config):
    dsn = config.registry.settings.get('sentry.dsn')

    if dsn is not None:
        configure_sentry_logger(dsn)
