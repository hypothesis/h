# pylint: disable=no-member # Instance of 'Celery' has no 'request' member
from h.celery import celery


@celery.task
def move_annotations_by_url(old_url, new_url_info):
    migration_svc = celery.request.find_service(name="url_migration")
    migration_svc.move_annotations_by_url(old_url, new_url_info)


@celery.task
def move_annotations(annotation_ids, current_uri_normalized, url_info):
    migration_svc = celery.request.find_service(name="url_migration")
    migration_svc.move_annotations(annotation_ids, current_uri_normalized, url_info)
