# pylint: disable=no-member # Instance of 'Celery' has no 'request' member
from h.celery import celery


@celery.task(rate_limit="10/m")
def move_annotations_by_url(old_url, new_url_info):
    migration_svc = celery.request.find_service(name="url_migration")
    migration_svc.move_annotations_by_url(old_url, new_url_info)


# nb. Each `move_annotations` task moves a batch of annotations, so the
# rate limit is `10 * batch_size` annotations per worker per minute.
@celery.task(rate_limit="10/m")
def move_annotations(annotation_ids, current_uri_normalized, url_info):
    migration_svc = celery.request.find_service(name="url_migration")
    migration_svc.move_annotations(annotation_ids, current_uri_normalized, url_info)
