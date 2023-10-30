from h.celery import celery, get_task_logger
from h.models import Annotation, AnnotationSlim
from h.services.annotation_write import AnnotationWriteService

log = get_task_logger(__name__)


@celery.task
def fill_annotation_slim(batch_size=1000):
    """Task to fill the new AnnotationSlim table in batches."""
    # pylint:disable=no-member

    anno_write_svc = celery.request.find_service(AnnotationWriteService)

    annotations = (
        celery.request.db.query(Annotation)
        .outerjoin(AnnotationSlim)
        .where(AnnotationSlim.pubid.is_(None), Annotation.deleted.is_(False))
        .order_by(Annotation.updated.desc())
        .limit(batch_size)
    )

    for annotation in annotations:
        anno_write_svc.upsert_annotation_slim(annotation)
