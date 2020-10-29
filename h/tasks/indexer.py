from datetime import datetime

import newrelic
from celery import Task

from h.celery import celery, get_task_logger
from h.models import Job

log = get_task_logger(__name__)


# See: https://docs.celeryproject.org/en/stable/userguide/tasks.html#automatic-retry-for-known-exceptions
class _BaseTaskWithRetry(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"countdown": 5, "max_retries": 1}


@celery.task(base=_BaseTaskWithRetry)
def add_annotation(id_):
    search_index = celery.request.find_service(name="search_index")
    search_index.add_annotation_by_id(id_)


@celery.task
def add_annotations_between_times(start_time, end_time, tag):
    search_index = celery.request.find_service(name="search_index")
    search_index._queue.add_between_times(start_time, end_time, tag)


@celery.task
def add_users_annotations(userid, tag, force, schedule_in):
    search_index = celery.request.find_service(name="search_index")
    search_index._queue.add_by_user(userid, tag, force=force, schedule_in=schedule_in)


@celery.task(base=_BaseTaskWithRetry)
def delete_annotation(id_):
    search_index = celery.request.find_service(name="search_index")
    search_index.delete_annotation_by_id(id_)


@celery.task(acks_late=False)
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


@celery.task(acks_late=False)
def report_job_queue_metrics():
    queue = celery.request.find_service(name="search_index")._queue

    now = datetime.utcnow()

    newrelic.agent.record_custom_metrics(
        [
            (
                "Custom/Job/Queue/Length",
                celery.request.db.query(Job).count(),
            ),
            (
                "Custom/Job/Queue/Expired/Length",
                celery.request.db.query(Job).filter(Job.expires_at < now).count(),
            ),
            (
                "Custom/SyncAnnotations/Queue/API/Length",
                queue.count(["storage.create_annotation", "storage.update_annotation"]),
            ),
        ]
    )
