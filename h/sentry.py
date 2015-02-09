import logging

from raven.base import Client
from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler


def configure_logger(client):
    """
    Configure the Sentry log handler using the provided Sentry client.
    """
    handler = SentryHandler(client, level=logging.WARN)
    setup_logging(handler)


def includeme(config):
    dsn = config.registry.settings.get('sentry.dsn')
    if dsn is None:
        return

    client = Client(dsn)
    configure_logger(client)
    config.registry.handle_exception = client.captureException
