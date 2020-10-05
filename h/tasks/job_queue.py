from h.celery import celery


@celery.task
def sync_annotations():
    celery.request.find_service(name="job_queue").sync_annotations()
