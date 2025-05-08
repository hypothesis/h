from sqlalchemy import exists, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import count

from h.models import Annotation, Notification, User
from h.models.notification import NotificationType
from h.services.user import UserService

# Limit for the number of notifications per annotation
NOTIFICATION_LIMIT = 100


class NotificationService:
    """A service for managing user notifications."""

    def __init__(self, session: Session, user_service: UserService) -> None:
        self._session = session
        self._user_service = user_service

    def allow_notifications(self, annotation: Annotation, user: User) -> bool:
        return (
            not self._notification_exists(annotation, user)
            and self._notification_count(annotation) < NOTIFICATION_LIMIT
        )

    def _notification_exists(self, annotation: Annotation, recipient: User) -> bool:
        """Check if a notification already exists for the given annotation and recipient."""
        self._session.flush()
        stmt = select(
            exists().where(
                Notification.source_annotation == annotation,
                Notification.recipient == recipient,
            )
        )
        return bool(self._session.execute(stmt).scalar())

    def _notification_count(self, annotation: Annotation) -> int:
        """Count the number of notifications for the given annotation."""
        stmt = select(count(Notification.id)).where(
            Notification.source_annotation == annotation
        )
        return self._session.execute(stmt).scalar() or 0

    def save_notification(
        self,
        annotation: Annotation,
        recipient: User,
        notification_type: NotificationType,
    ) -> Notification:
        notification = Notification(
            source_annotation=annotation,
            recipient=recipient,
            notification_type=notification_type,
        )
        self._session.add(notification)
        return notification


def factory(_context, request) -> NotificationService:
    """Return a NotificationService instance for the passed context and request."""
    return NotificationService(
        session=request.db,
        user_service=request.find_service(name="user"),
    )
