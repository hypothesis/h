from h.tasks.celery import celery, get_task_logger

log = get_task_logger(__name__)


@celery.task
def add_annotations_between_times(name, start_time, end_time, tag):
    celery.request.find_service(name="queue_service").add_between_times(
        name, start_time, end_time, tag
    )


@celery.task
def add_annotations_from_user(name, userid, tag, force=False, schedule_in=None):
    celery.request.find_service(name="queue_service").add_by_user(
        name, userid, tag, force=force, schedule_in=schedule_in
    )


@celery.task
def add_annotations_from_group(name, groupid, tag, force=False, schedule_in=None):
    celery.request.find_service(name="queue_service").add_by_group(
        name, groupid, tag, force=force, schedule_in=schedule_in
    )


@celery.task
def add_annotations_by_ids(
    name, annotation_ids: list[str], tag, force=False, schedule_in=None
):
    celery.request.find_service(name="queue_service").add_by_ids(
        name, annotation_ids, tag, force=force, schedule_in=schedule_in
    )
