from datetime import datetime

from sqlalchemy import select

from h.models import ModerationLog, ModerationStatus
from h.models.notification import NotificationType
from h.tasks.celery import celery, get_task_logger
from h.services.notification import NotificationService

log = get_task_logger(__name__)


@celery.task
def send_moderation_email(annotation_id, moderation_datetime_iso: str):
    db = celery.request.db

    print("send_moderation_email", annotation_id, moderation_datetime_iso)
    moderation_datetime = datetime.fromisoformat(moderation_datetime_iso)

    moderation_log = db.scalars(
        select(ModerationLog)
        .where(
            ModerationLog.annotation_id == annotation_id,
            ModerationLog.created >= moderation_datetime,
            ModerationLog.notification_id.is_(None),
        )
        .order_by(ModerationLog.created.asc())
        .with_for_update(skip_locked=True)
    ).all()

    if not moderation_log:
        log.info(
            "No moderation log found for annotation %s after %s",
            annotation_id,
            moderation_datetime,
        )
        return

    if moderation_log[-1].created > moderation_datetime:
        log.info(
            "Moderation changes made after %s for annotation %s",
            annotation_id,
            moderation_datetime,
        )
        return

    old_status = moderation_log[0].old_moderation_status
    new_status = moderation_log[-1].new_moderation_status
    print(moderation_log[0].id)
    print(moderation_log[-1].id)
    print(old_status, new_status)

    if old_status == new_status:
        log.info(
            "Moderation changes resulted in no status change for annotation %s",
            annotation_id,
        )
        return

    email_sending_status_changes = {
        (ModerationStatus.PENDING, ModerationStatus.APPROVED),
        (ModerationStatus.PENDING, ModerationStatus.DENIED),
        (ModerationStatus.APPROVED, ModerationStatus.PENDING),
        (ModerationStatus.APPROVED, ModerationStatus.DENIED),
        (ModerationStatus.DENIED, ModerationStatus.APPROVED),
        (ModerationStatus.SPAM, ModerationStatus.APPROVED),
    }

    if (old_status, new_status) not in email_sending_status_changes:
        log.info(
            "No email sent for annotation %s for transition from %s to %s",
            annotation_id,
            old_status,
            new_status,
        )
        return

    annotation = moderation_log[0].annotation
    notification_service = celery.request.find_service(NotificationService)
    user_service = celery.request.find_service(name="user")
    user = user_service.fetch(annotation.userid)
    notification = notification_service.save_notification(
        annotation=annotation,
        recipient=user,
        notification_type=NotificationType.ANNOTATION_MODERATED,
    )
    # All these rows are affected by the same notification
    for log_entry in moderation_log:
        log_entry.notification = notification

    log.info(
        "Sending moderation email for annotation %s for transition from %s to %s",
        annotation_id,
        old_status,
        new_status,
    )
