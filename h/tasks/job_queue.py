# pylint: disable=no-member # Instance of 'Celery' has no 'request' member


from h.celery import celery, get_task_logger

log = get_task_logger(__name__)


@celery.task
def add_annotations_between_times(start_time, end_time, tag):
    celery.request.find_service(name="queue_service").add_between_times(
        start_time, end_time, tag
    )


@celery.task
def add_annotations_from_user(userid, tag, force, schedule_in):
    celery.request.find_service(name="queue_service").add_by_user(
        userid, tag, force=force, schedule_in=schedule_in
    )


@celery.task
def add_annotations_from_group(groupid, tag, force, schedule_in):
    celery.request.find_service(name="queue_service").add_by_group(
        groupid, tag, force=force, schedule_in=schedule_in
    )
