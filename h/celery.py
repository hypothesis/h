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

from h.tasks import RETRY_POLICY_QUICK

log = logging.getLogger(__name__)

celery = Celery("h")
celery.conf.update(
    broker_url=os.environ.get(
        "CELERY_BROKER_URL",
        os.environ.get("BROKER_URL", "amqp://guest:guest@localhost:5672//"),
    ),
    # What options should we have when sending messages to the queue?
    broker_transport_options=RETRY_POLICY_QUICK,
    accept_content=["json"],
    # Enable at-least-once delivery mode. This probably isn't actually what we
    # want for all of our queues, but it makes the failure-mode behaviour of
    # Celery the same as our old NSQ worker:
    task_acks_late=True,
    worker_disable_rate_limits=True,
    task_ignore_result=True,
    imports=("h.tasks.cleanup", "h.tasks.indexer", "h.tasks.mailer"),
    task_routes={
        "h.tasks.indexer.add_annotation": "indexer",
        "h.tasks.indexer.add_annotations_between_times": "indexer",
        "h.tasks.indexer.add_group_annotations": "indexer",
        "h.tasks.indexer.add_users_annotations": "indexer",
        "h.tasks.indexer.delete_annotation": "indexer",
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
)


@signals.worker_init.connect
def bootstrap_worker(sender, **_kwargs):
    request = sender.app.webapp_bootstrap()
    sender.app.request = request


@signals.task_prerun.connect
def reset_nipsa_cache(sender, **_kwargs):
    """Reset nipsa service cache before running each task."""
    svc = sender.app.request.find_service(name="nipsa")
    svc.clear()


@signals.task_success.connect
def transaction_commit(sender, **_kwargs):
    """Commit the request transaction after each successful task execution."""
    sender.app.request.tm.commit()


@signals.task_failure.connect
def transaction_abort(sender, **_kwargs):
    """Abort the request transaction after each failed task execution."""
    sender.app.request.tm.abort()


@signals.task_failure.connect
def report_failure(sender, task_id, args, kwargs, einfo, **_kwargs):
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


@signals.task_prerun.connect
def add_task_name_and_id_to_log_messages(
    task_id, task, *_args, **_kwargs
):  # pragma: no cover
    """
     Add the Celery task name and ID to all messages logged by Celery tasks.

     This makes it easier to observe Celery tasks by reading the logs. For
     example you can find all messages logged by a given Celery task by
     searching for the task's name in the logs.

     This affects:

    * Logging by Celery itself
    * Logging in our @celery.task functions or anything they call (directly
      or indirectly)
    """
    # Replace the root logger's formatter with one that includes task.name and
    # task_id in the format. This assumes that the root logger has one handler,
    # which happens to be the case.
    root_loggers_handler = logging.getLogger().handlers[0]

    root_loggers_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s: %(levelname)s/%(processName)s] "
            + f"{task.name}[{task_id}] "
            + "%(message)s"
        )
    )
