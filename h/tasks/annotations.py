from h.celery import celery, get_task_logger
from h.db.types import URLSafeUUID
from h.models import Annotation
from h.services.annotation_write import AnnotationWriteService

log = get_task_logger(__name__)


@celery.task
def sync_annotation_slim(limit):
    """Process jobs to fill the new AnnotationSlim table in batches."""
    # pylint:disable=no-member
    anno_write_svc = celery.request.find_service(AnnotationWriteService)
    queue_svc = celery.request.find_service(name="queue_service")

    # Get pending jobs, up to `limit`
    jobs = queue_svc.get(name="annotation_slim", limit=limit)
    if not jobs:
        return

    # Gather all the annotation IDs on the jobs
    annotation_ids = {
        URLSafeUUID.hex_to_url_safe(job.kwargs["annotation_id"]) for job in jobs
    }

    # Build a dictionary Id -> Annotation querying all annotations in one go
    annotations_from_db = {
        annotation.id: annotation
        for annotation in celery.request.db.query(Annotation)
        .filter_by(deleted=False)
        .filter(Annotation.id.in_(annotation_ids))
    }

    for job in jobs:
        # For each job, insert the row in annotation slim
        annotation_id = URLSafeUUID.hex_to_url_safe(job.kwargs["annotation_id"])
        if annotation := annotations_from_db.get(annotation_id):
            anno_write_svc.upsert_annotation_slim(annotation)

    # Remove all jobs we've processed
    queue_svc.delete(jobs)
