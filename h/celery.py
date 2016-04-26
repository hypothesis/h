# -*- coding: utf-8 -*-

"""
Celery worker bootstrap and configuration.

This module configures a Celery application for processing background jobs, and
integrates it with the Pyramid application by attaching a bootstrapped fake
"request" object to the application where it can be retrieved by tasks.
"""

from __future__ import absolute_import

import logging
import os

from celery import Celery
from celery import signals
from celery.utils.log import get_task_logger
from pyramid import paster
from pyramid.request import Request
from raven.contrib.celery import register_signal, register_logger_signal

__all__ = (
    'celery',
    'get_task_logger',
)

log = logging.getLogger(__name__)

celery = Celery('h')
celery.conf.update(
    # Default to using database number 10 so we don't conflict with the session
    # store.
    BROKER_URL=os.environ.get('CELERY_BROKER_URL',
        os.environ.get('BROKER_URL', 'amqp://guest:guest@localhost:5672//')),
    CELERY_ACCEPT_CONTENT=['json'],
    # Enable at-least-once delivery mode. This probably isn't actually what we
    # want for all of our queues, but it makes the failure-mode behaviour of
    # Celery the same as our old NSQ worker:
    CELERY_ACKS_LATE=True,
    CELERY_DISABLE_RATE_LIMITS=True,
    CELERY_IGNORE_RESULT=True,
    CELERY_IMPORTS=('h.mailer', 'h.nipsa.worker', 'h.indexer'),
    CELERY_ROUTES={
        'h.indexer.add_annotation': 'indexer',
        'h.indexer.delete_annotation': 'indexer',
    },
    CELERY_TASK_SERIALIZER='json',
    # Only accept one task at a time. This also probably isn't what we want
    # (especially not for, say, a search indexer task) but it makes the
    # behaviour consistent with the previous NSQ-based worker:
    CELERYD_PREFETCH_MULTIPLIER=1,
)


@signals.worker_init.connect
def bootstrap_worker(sender, **kwargs):
    base_url = os.environ.get('APP_URL')
    config_uri = os.environ.get('CONFIG_URI', 'conf/app.ini')

    paster.setup_logging(config_uri)

    if base_url is None:
        base_url = 'http://localhost'
        log.warn('APP_URL not found in environment, using default: %s',
                 base_url)

    request = Request.blank('/', base_url=base_url)
    env = paster.bootstrap(config_uri, request=request)
    request.root = env['root']

    sender.app.request = request

    # Configure Sentry reporting on task failure
    register_signal(request.sentry)
    register_logger_signal(request.sentry, loglevel=logging.ERROR)


@signals.task_prerun.connect
def reset_feature_flags(sender, **kwargs):
    """Reset feature flags before running each task."""
    sender.app.request.feature.clear()


@signals.task_success.connect
def transaction_commit(sender, **kwargs):
    """Commit the request transaction after each successful task execution."""
    sender.app.request.tm.commit()


@signals.task_failure.connect
def transaction_abort(sender, **kwargs):
    """Abort the request transaction after each failed task execution."""
    sender.app.request.tm.abort()


def main():
    celery.start()
