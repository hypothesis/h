"""
Celery worker bootstrap and configuration.

This module configures a Celery application for processing background jobs, and
integrates it with the Pyramid application by attaching a bootstrapped fake
"request" object to the application where it can be retrieved by tasks.
"""

import logging
import os

from celery import Celery, signals
from celery.utils.log import get_task_logger
from kombu import Exchange, Queue

__all__ = ("celery", "get_task_logger")

log = logging.getLogger(__name__)

celery = Celery("h")
celery.conf.update(
    broker_url=os.environ.get(
        "CELERY_BROKER_URL",
        os.environ.get("BROKER_URL", "amqp://guest:guest@localhost:5672//"),
    ),
    accept_content=["json"],
    # Enable at-least-once delivery mode. This probably isn't actually what we
    # want for all of our queues, but it makes the failure-mode behaviour of
    # Celery the same as our old NSQ worker:
    task_acks_late=True,
    worker_disable_rate_limits=True,
    task_ignore_result=True,
    imports=("h.tasks.admin", "h.tasks.cleanup", "h.tasks.indexer", "h.tasks.mailer"),
    task_routes={
        "h.tasks.indexer.add_annotation": "indexer",
        "h.tasks.indexer.delete_annotation": "indexer",
        "h.tasks.indexer.reindex_user_annotations": "indexer",
    },
    task_serializer="json",
    task_queues=[
        Queue(
            "celery",
            durable=True,
            routing_key="celery",
            exchange=Exchange("celery", type="direct", durable=True),
        ),
        Queue(
            "indexer",
            durable=True,
            routing_key="indexer",
            exchange=Exchange("indexer", type="direct", durable=True),
        ),
    ],
    # Only accept one task at a time. This also probably isn't what we want
    # (especially not for, say, a search indexer task) but it makes the
    # behaviour consistent with the previous NSQ-based worker:
    worker_prefetch_multiplier=1,
    # Suggestions from: https://www.cloudamqp.com/docs/celery.html
    # Will decrease connection usage
    broker_pool_limit=1,
    # We're using TCP keep-alive instead
    broker_heartbeat=None,
    # May require a long timeout due to Linux DNS timeouts etc
    broker_connection_timeout=30,
    # AMQP is not recommended as result backend as it creates thousands of
    # queues
    result_backend=None,
    # Will delete all celeryev. queues without consumers after 1 minute.
    event_queue_expires=60,
    # Disable prefetching, it's causes problems and doesn't help performance
    # worker_prefetch_multiplier=1, (duplicated above)
    # If you tasks are CPU bound, then limit to the number of cores, otherwise
    # increase substainally
    worker_concurrency=50,
)


@signals.worker_init.connect
def bootstrap_worker(sender, **kwargs):
    request = sender.app.webapp_bootstrap()
    sender.app.request = request


@signals.task_prerun.connect
def reset_nipsa_cache(sender, **kwargs):
    """Reset nipsa service cache before running each task."""
    svc = sender.app.request.find_service(name="nipsa")
    svc.clear()


@signals.task_success.connect
def transaction_commit(sender, **kwargs):
    """Commit the request transaction after each successful task execution."""
    sender.app.request.tm.commit()


@signals.task_failure.connect
def transaction_abort(sender, **kwargs):
    """Abort the request transaction after each failed task execution."""
    sender.app.request.tm.abort()


@signals.task_failure.connect
def report_failure(sender, task_id, args, kwargs, einfo, **kw):
    """Report a task failure to the console in development."""
    if not sender.app.request.debug:
        return
    log.error(
        "task failure: %s (%s) called with args=%s, kwargs=%s",
        sender.name,
        task_id,
        args,
        kwargs,
        exc_info=einfo.exc_info,
    )


def start(argv, bootstrap):
    """Run the Celery CLI."""
    # We attach the bootstrap function directly to the Celery application
    # instance, and it's then used in the worker bootstrap subscriber above.
    celery.webapp_bootstrap = bootstrap
    celery.start(argv)
