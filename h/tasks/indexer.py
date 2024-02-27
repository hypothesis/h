# pylint: disable=no-member # Instance of 'Celery' has no 'request' member
from abc import ABC

import newrelic
from celery import Task

from h.celery import celery, get_task_logger
from h.services import AnnotationSyncService

log = get_task_logger(__name__)


# See: https://docs.celeryproject.org/en/stable/userguide/tasks.html#automatic-retry-for-known-exceptions
class _BaseTaskWithRetry(ABC, Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"countdown": 5, "max_retries": 1}


@celery.task(base=_BaseTaskWithRetry, acks_late=True)
def add_annotation(id_):
    search_index = celery.request.find_service(name="search_index")
    search_index.add_annotation_by_id(id_)


@celery.task(base=_BaseTaskWithRetry, acks_late=True)
def delete_annotation(id_):
    search_index = celery.request.find_service(name="search_index")
    search_index.delete_annotation_by_id(id_)


@celery.task
def sync_annotations(limit):
    annotation_sync_service = celery.request.find_service(AnnotationSyncService)

    counts = annotation_sync_service.sync(limit)

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
