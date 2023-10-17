from sqlalchemy import func, insert

from h.celery import celery, get_task_logger
from h.models import Annotation, AnnotationModeration, AnnotationSlim, Group, User

log = get_task_logger(__name__)


@celery.task
def fill_annotation_slim(batch_size=1000):
    """Task to fill the new AnnotationSlim table in batches."""
    # pylint: disable=no-member
    db = celery.request.db

    annotations = (
        db.query(
            Annotation.id.label("pubid"),
            Annotation.created,
            Annotation.updated,
            Annotation.deleted,
            Annotation.shared,
            Annotation.document_id,
            Group.id.label("group_id"),
            User.id.label("user_id"),
            AnnotationModeration.id.is_not(None).label("moderated"),
        )
        .join(Group, Group.pubid == Annotation.groupid)
        .join(
            User,
            User.username
            == func.split_part(func.split_part(Annotation.userid, "@", 1), ":", 2),
        )
        .outerjoin(AnnotationSlim)
        .outerjoin(AnnotationModeration)
        .where(AnnotationSlim.id.is_(None))
        .order_by(Annotation.updated.desc())
        .limit(batch_size)
    ).cte("annotations")

    db.execute(
        insert(AnnotationSlim).from_select(
            [
                annotations.c.pubid,
                annotations.c.created,
                annotations.c.updated,
                annotations.c.deleted,
                annotations.c.shared,
                annotations.c.document_id,
                annotations.c.group_id,
                annotations.c.user_id,
                annotations.c.moderated,
            ],
            annotations,
        )
    )
