from h.celery import celery, get_task_logger
from h.models import Annotation
from sqlalchemy import update

log = get_task_logger(__name__)


@celery.task
def fill_pk_value(batch_size=10):
    # pylint: disable=no-member
    with celery.request.tm:
        db = celery.request.db

        annotations = (
            db.query(Annotation.id)
            .where(Annotation.pk == None)
            .order_by(Annotation.updated.asc())
            .limit(batch_size)
        ).cte("annotations")

        db.execute(
            update(Annotation)
            .values(pk=Annotation.pk_sequence.next_value())
            .where(Annotation.id == annotations.c.id)
        )
