"""Temporary Celery tasks that can be deleted once they're no longer needed."""

import os

from sqlalchemy.sql.expression import func

from h.celery import celery, get_task_logger
from h.models import Annotation

log = get_task_logger(__name__)


@celery.task
def backfill_annotation_sequence_ids():
    """
    Temporary task to back-fill the annotation.sequence_id column.

    This task can be deleted once the column has been back-filled in the
    production DB.
    """
    db = celery.request.db
    limit = os.environ.get("BACKFILL_ANNOTATIONS_LIMIT", 1000)

    annotations = (
        db.query(Annotation)
        .filter_by(sequence_id=None)
        .order_by(Annotation.created)
        .limit(limit)
    )

    sequence_id = (
        db.query(func.max(Annotation.sequence_id))
        .filter(Annotation.sequence_id < 15000000)
        .scalar()
    )

    if sequence_id is None:
        sequence_id = 0
    else:
        sequence_id += 1

    num_annotations = annotations.count()

    if num_annotations:
        log.info(
            f"Backfilling sequence_id's for {annotations.count()} annotations "
            f"starting from sequence_id {sequence_id} "
            f"and created date {annotations.first().created}"
        )
    else:
        # Once it starts logging this message it's time to delete this task
        # from the code.
        log.info("No more annotations to backfill")

    for annotation in annotations:
        annotation.sequence_id = sequence_id
        sequence_id += 1
