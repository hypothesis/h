from sqlalchemy import func, update

from h.celery import celery, get_task_logger
from h.models import Annotation, User

log = get_task_logger(__name__)


@celery.task
def fill_pk_and_user_id(batch_size=1000):
    """
    Task to fill the new annotation.pk and annotation.user_id in batches.

    Once most of the existing rows are done we'll make the code changes
    to keep these up to date, make the column not nullable and remove this task.
    """
    # pylint: disable=no-member
    db = celery.request.db

    annotations = (
        db.query(Annotation.id.label("annotation_id"), User.id.label("user_id"))
        .join(
            User,
            User.username
            == func.split_part(func.split_part(Annotation.userid, "@", 1), ":", 2),
        )
        .where(Annotation.pk.is_(None))
        .order_by(Annotation.updated.asc())
        .limit(batch_size)
    ).cte("annotations")

    db.execute(
        update(Annotation)
        .values(pk=Annotation.pk_sequence.next_value(), user_id=annotations.c.user_id)
        .where(Annotation.id == annotations.c.annotation_id)
        # just update the rows in the DB, we don't need to refresh the objects in the session
        .execution_options(synchronize_session=False)
    )
