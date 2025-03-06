from sqlalchemy import exists, select
from sqlalchemy.sql.functions import count

from h.db import Session
from h.models import Annotation, Notification, User
from h.models.notification import NotificationType
from h.services.user import UserService

NOTIFICATION_LIMIT = 100


class NotificationService:
    """A service for managing user notifications."""

    def __init__(self, session: Session, user_service: UserService) -> None:
        self._session = session
        self._user_service = user_service

    def allow_notifications(self, annotation: Annotation, user: User) -> bool:
        return (
            not self.notification_exists(annotation, user)
            and self.notification_count(annotation) < NOTIFICATION_LIMIT
        )

    def notification_exists(self, annotation: Annotation, recipient: User) -> bool:
        self._session.flush()
        stmt = select(
            exists().where(
                Notification.source_annotation == annotation,
                Notification.recipient == recipient,
            )
        )
        return self._session.execute(stmt).scalar()

    def notification_count(self, annotation: Annotation) -> int:
        stmt = select(count(Notification.id)).where(
            Notification.source_annotation == annotation
        )
        return self._session.execute(stmt).scalar()

    def save_notification(
        self,
        annotation: Annotation,
        recipient: User,
        notification_type: NotificationType,
    ) -> None:
        notification = Notification(
            source_annotation=annotation,
            recipient=recipient,
            notification_type=notification_type,
        )
        self._session.add(notification)


def factory(_context, request) -> NotificationService:
    """Return a NotificationService instance for the passed context and request."""
    return NotificationService(
        session=request.db,
        user_service=request.find_service(name="user"),
    )
