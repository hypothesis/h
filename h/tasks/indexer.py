# pylint: disable=no-member # Instance of 'Celery' has no 'request' member
from abc import ABC

import newrelic
from celery import Task

from h.celery import celery, get_task_logger

log = get_task_logger(__name__)


# See: https://docs.celeryproject.org/en/stable/userguide/tasks.html#automatic-retry-for-known-exceptions
class _BaseTaskWithRetry(ABC, Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"countdown": 5, "max_retries": 1}


@celery.task(base=_BaseTaskWithRetry, acks_late=True)
def add_annotation(id_):
    search_index = celery.request.find_service(name="search_index")
    search_index.add_annotation_by_id(id_)


@celery.task
def add_annotations_between_times(start_time, end_time, tag):
    search_index = celery.request.find_service(name="search_index")
    search_index._queue.add_between_times(  # pylint: disable=protected-access
        start_time, end_time, tag
    )


@celery.task
def add_users_annotations(userid, tag, force, schedule_in):
    search_index = celery.request.find_service(name="search_index")
    search_index._queue.add_by_user(  # pylint: disable=protected-access
        userid, tag, force=force, schedule_in=schedule_in
    )


@celery.task
def add_group_annotations(groupid, tag, force, schedule_in):
    search_index = celery.request.find_service(name="search_index")
    search_index._queue.add_by_group(  # pylint: disable=protected-access
        groupid, tag, force=force, schedule_in=schedule_in
    )


@celery.task(base=_BaseTaskWithRetry, acks_late=True)
def delete_annotation(id_):
    search_index = celery.request.find_service(name="search_index")
    search_index.delete_annotation_by_id(id_)


@celery.task
def sync_annotations(limit):
    search_index = celery.request.find_service(name="search_index")

    counts = search_index.sync(limit)

    log.info(dict(counts))
    newrelic.agent.record_custom_metrics(
        [
            (f"Custom/SyncAnnotations/Queue/{key}", value)
            for key, value in counts.items()
        ]
    )


@celery.task
def report_job_queue_metrics():
    metrics = celery.request.find_service(name="job_queue_metrics").metrics()
    newrelic.agent.record_custom_metrics(metrics)
