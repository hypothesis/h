from unittest.mock import sentinel

import pytest

from h.models.notification import NotificationType
from h.services.notification import NotificationService, factory


class TestNotificationService:
    def test_allow_notifications(self, service, annotation, user):
        assert service.allow_notifications(annotation, user)

    def test_dont_allow_notifications_when_notification_exists(
        self, service, annotation, user
    ):
        service.save_notification(annotation, user, NotificationType.MENTION)

        assert not service.allow_notifications(annotation, user)

    def test_dont_allow_notifications_when_limit_reached(
        self, service, annotation, user, patch
    ):
        patch("h.services.notification.NOTIFICATION_LIMIT", new=1, autospec=False)
        service.save_notification(annotation, user, NotificationType.MENTION)

        assert not service.allow_notifications(annotation, user)

    def test_notification_exists(self, service, annotation, user):
        service.save_notification(annotation, user, NotificationType.MENTION)

        assert service._notification_exists(annotation, user)  # noqa: SLF001

    def test_notification_doesnt_exist(self, service, annotation, user):
        assert not service._notification_exists(annotation, user)  # noqa: SLF001

    def test_notification_count(self, service, annotation, user):
        service.save_notification(annotation, user, NotificationType.MENTION)

        assert service._notification_count(annotation) == 1  # noqa: SLF001

    def test_save_notification(self, service, annotation, user):
        service.save_notification(annotation, user, NotificationType.REPLY)

        assert service._notification_exists(annotation, user)  # noqa: SLF001
        assert service._notification_count(annotation) == 1  # noqa: SLF001

    @pytest.fixture
    def annotation(self, factories, user):
        return factories.Annotation(userid=user.userid)

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def service(self, db_session, user_service):
        return NotificationService(db_session, user_service)


class TestFactory:
    def test_it(self, pyramid_request, user_service, NotificationService):
        service = factory(sentinel.context, pyramid_request)

        NotificationService.assert_called_once_with(
            session=pyramid_request.db,
            user_service=user_service,
        )

        assert service == NotificationService.return_value

    @pytest.fixture
    def NotificationService(self, patch):
        return patch("h.services.notification.NotificationService")
