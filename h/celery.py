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
    broker_transport_options={
        # Celery's docs are very unclear about this but: when publishing a
        # message to RabbitMQ these options end up getting passed to Kombu's
        # _ensure_connection() function:
        # https://github.com/celery/kombu/blob/3e098dc94ed2a389276ccf3606a0ded3da157d72/kombu/connection.py#L399-L453
        #
        # By default _ensure_connection() can spend over 6s trying to establish
        # a connection to RabbitMQ if RabbitMQ is down. This means that if
        # RabbitMQ goes down then all of our web processes can quickly become
        # occupied trying to establish connections when web requests try to
        # call Celery tasks with .delay() or .apply_async().
        #
        # These options change it to use a smaller number of retries and less
        # time between retries so that attempts fail fast when RabbitMQ is down
        # and our whole web app remains responsive.
        #
        # For more info see: https://github.com/celery/celery/issues/4627#issuecomment-396907957
        "max_retries": 2,
        "interval_start": 0.2,
        "interval_step": 0.2,
    },
    # Tell Celery to kill any task run (by raising
    # celery.exceptions.SoftTimeLimitExceeded) if it takes longer than
    # task_soft_time_limit seconds.
    #
    # See: https://docs.celeryq.dev/en/stable/userguide/workers.html#time-limits
    #
    # This is to protect against task runs hanging forever which blocks a
    # Celery worker and prevents Celery retries from kicking in.
    #
    # This can be overridden on a per-task basis by adding soft_time_limit=n to
    # the task's @app.task() arguments.
    #
    # We're using soft rather than hard time limits because hard time limits
    # don't trigger Celery retries whereas soft ones do. Soft time limits also
    # give the task a chance to catch SoftTimeLimitExceeded and do some cleanup
    # before exiting.
    task_soft_time_limit=120,
    # Tell Celery to force-terminate any task run (by terminating the worker
    # process and replacing it with a new one) if it takes linger than
    # task_time_limit seconds.
    #
    # This is needed to defend against tasks hanging during cleanup: if
    # task_soft_time_limit expires the task can catch SoftTimeLimitExceeded and
    # could then hang again in the exception handler block. task_time_limit
    # ensures that the task is force-terminated in that case.
    #
    # This can be overridden on a per-task basis by adding time_limit=n to the
    # task's @app.task() arguments.
    task_time_limit=240,
    # Disable Celery task rate limits in local development.
    worker_disable_rate_limits=os.environ.get("DEV") == "true",
    imports=(
        "h.tasks.annotations",
        "h.tasks.cleanup",
        "h.tasks.indexer",
        "h.tasks.mailer",
        "h.tasks.url_migration",
    ),
    task_routes={
        "h.tasks.indexer.add_annotation": "indexer",
        "h.tasks.indexer.add_annotations_between_times": "indexer",
        "h.tasks.indexer.add_group_annotations": "indexer",
        "h.tasks.indexer.add_users_annotations": "indexer",
        "h.tasks.indexer.delete_annotation": "indexer",
    },
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


def start(argv, bootstrap):  # pragma: no cover
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
