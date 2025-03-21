from unittest import mock
from unittest.mock import call, create_autospec, sentinel

import pytest
from kombu.exceptions import OperationalError
from transaction import TransactionManager

from h import __version__, subscribers
from h.events import AnnotationEvent
from h.exceptions import RealtimeMessageQueueError
from h.models.notification import NotificationType
from h.tasks import mailer


@pytest.mark.usefixtures("routes")
class TestAddRendererGlobals:
    def test_adds_base_url(self, event):
        subscribers.add_renderer_globals(event)

        assert event["base_url"] == "http://example.com/idx"

    def test_adds_feature_flag_client(self, event, pyramid_request):
        subscribers.add_renderer_globals(event)

        assert event["feature"] == pyramid_request.feature

    def test_adds_analytics_tracking_id(self, event, pyramid_request):
        pyramid_request.registry.settings["google_analytics_measurement_id"] = (
            "abcd1234"
        )

        subscribers.add_renderer_globals(event)

        assert event["google_analytics_measurement_id"] == "abcd1234"

    def test_adds_frontend_settings(self, event):
        subscribers.add_renderer_globals(event)
        assert event["frontend_settings"] == {}

    @pytest.mark.usefixtures("sentry_config")
    def test_adds_frontend_settings_sentry(self, event):
        subscribers.add_renderer_globals(event)

        assert event["frontend_settings"]["sentry"] == {
            "dsn": "https://sentry.io/flibble",
            "environment": "prod",
            "release": __version__,
            "userid": None,
        }

    @pytest.mark.usefixtures("sentry_config")
    def test_adds_frontend_settings_sentry_userid(
        self,
        event,
        pyramid_config,
    ):
        pyramid_config.testing_securitypolicy("acct:safet.baljić@example.com")

        subscribers.add_renderer_globals(event)
        result = event["frontend_settings"]["sentry"]["userid"]

        assert result == "acct:safet.baljić@example.com"

    @pytest.fixture
    def event(self, pyramid_request):
        return {"request": pyramid_request}

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("index", "/idx")

    @pytest.fixture
    def sentry_config(self, pyramid_request):
        settings = pyramid_request.registry.settings
        settings["h.sentry_dsn_frontend"] = "https://sentry.io/flibble"
        settings["h.sentry_environment"] = "prod"


class TestPublishAnnotationEvent:
    def test_it_publishes_the_realtime_event(self, event):
        event.request.headers = {"X-Client-Id": "client_id"}

        subscribers.publish_annotation_event(event)

        event.request.realtime.publish_annotation.assert_called_once_with(
            {
                "action": event.action,
                "annotation_id": event.annotation_id,
                "src_client_id": "client_id",
            }
        )

    def test_it_exits_cleanly_when_RealtimeMessageQueueError_is_raised(self, event):
        event.request.realtime.publish_annotation.side_effect = (
            RealtimeMessageQueueError
        )

        subscribers.publish_annotation_event(event)

    def test_it_raises_for_other_errors(self, event):
        event.request.realtime.publish_annotation.side_effect = EnvironmentError

        with pytest.raises(EnvironmentError):  # noqa: PT011
            subscribers.publish_annotation_event(event)

    @pytest.fixture
    def event(self, pyramid_request):
        pyramid_request.realtime = mock.Mock()
        event = AnnotationEvent(pyramid_request, "test_annotation_id", "create")
        return event


@pytest.mark.usefixtures("annotation_read_service", "notification_service")
class TestSendReplyNotifications:
    def test_it_sends_emails(
        self,
        event,
        pyramid_request,
        annotation_read_service,
        notification_service,
        reply,
        mention,
        emails,
        tasks_mailer,
        asdict,
        LogData,
    ):
        subscribers.send_reply_notifications(event)

        # This is a pure plumbing test, checking everything is connected to
        # everything else as we expect

        annotation_read_service.get_annotation_by_id.assert_called_once_with(
            event.annotation_id
        )
        annotation = annotation_read_service.get_annotation_by_id.return_value

        reply.get_notification.assert_called_once_with(
            pyramid_request, annotation, event.action
        )
        notification = reply.get_notification.return_value

        emails.reply_notification.generate.assert_called_once_with(
            pyramid_request, notification
        )

        mention.get_notifications.assert_called_once_with(
            pyramid_request, annotation, event.action
        )

        notification_service.allow_notifications.assert_called_once_with(
            annotation, notification.parent_user
        )

        email_data = emails.reply_notification.generate.return_value
        asdict.assert_has_calls([call(email_data), call(LogData.return_value)])
        tasks_mailer.send.delay.assert_called_once_with(
            sentinel.email_data, sentinel.log_data
        )

        notification_service.save_notification.assert_called_once_with(
            annotation=annotation,
            recipient=notification.parent_user,
            notification_type=NotificationType.REPLY,
        )

    def test_it_does_nothing_if_no_notification_is_required(
        self, event, reply, tasks_mailer
    ):
        reply.get_notification.return_value = None

        subscribers.send_reply_notifications(event)

        tasks_mailer.send.delay.assert_not_called()

    def test_it_fails_gracefully_if_the_task_does_not_queue(self, event, tasks_mailer):
        tasks_mailer.send.side_effect = OperationalError

        # No explosions please
        subscribers.send_reply_notifications(event)

    def test_it_does_nothing_if_the_reply_user_is_mentioned(
        self, event, reply, tasks_mailer, mention
    ):
        reply_notification = mock.MagicMock()
        reply.get_notification.return_value = reply_notification

        mention_notifications = [mock.MagicMock()]
        mention.get_notifications.return_value = mention_notifications
        mention_notifications[0].mentioned_user = reply_notification.parent_user

        subscribers.send_reply_notifications(event)

        tasks_mailer.send.delay.assert_not_called()

    def test_it_does_nothing_if_notifications_arent_allowed(
        self, event, tasks_mailer, notification_service
    ):
        notification_service.allow_notifications.return_value = False

        subscribers.send_reply_notifications(event)

        tasks_mailer.send.delay.assert_not_called()

    @pytest.fixture
    def event(self, pyramid_request):
        return AnnotationEvent(pyramid_request, {"id": "any"}, "action")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.tm = mock.MagicMock()
        return pyramid_request


@pytest.mark.usefixtures("annotation_read_service", "notification_service")
class TestSendMentionNotifications:
    def test_it_sends_emails(
        self,
        event,
        pyramid_request,
        annotation_read_service,
        notification_service,
        mention,
        emails,
        tasks_mailer,
        asdict,
        LogData,
    ):
        notifications = mention.get_notifications.return_value

        subscribers.send_mention_notifications(event)

        # This is a pure plumbing test, checking everything is connected to
        # everything else as we expect

        annotation_read_service.get_annotation_by_id.assert_called_once_with(
            event.annotation_id
        )
        annotation = annotation_read_service.get_annotation_by_id.return_value

        mention.get_notifications.assert_called_once_with(
            pyramid_request, annotation, event.action
        )

        emails.mention_notification.generate.assert_called_once_with(
            pyramid_request, notifications[0]
        )

        notification_service.allow_notifications.assert_called_once_with(
            annotation, notifications[0].mentioned_user
        )

        email_data = emails.mention_notification.generate.return_value
        asdict.assert_has_calls([call(email_data), call(LogData.return_value)])
        tasks_mailer.send.delay.assert_called_once_with(
            sentinel.email_data, sentinel.log_data
        )

        notification_service.save_notification.assert_called_once_with(
            annotation=annotation,
            recipient=notifications[0].mentioned_user,
            notification_type=NotificationType.MENTION,
        )

    def test_it_does_nothing_if_no_notification_is_required(
        self, event, mention, tasks_mailer
    ):
        mention.get_notifications.return_value = []

        subscribers.send_mention_notifications(event)

        tasks_mailer.send.delay.assert_not_called()

    def test_it_fails_gracefully_if_the_task_does_not_queue(self, event, tasks_mailer):
        tasks_mailer.send.side_effect = OperationalError

        # No explosions please
        subscribers.send_mention_notifications(event)

    def test_it_does_nothing_if_notifications_arent_allowed(
        self, event, tasks_mailer, notification_service
    ):
        notification_service.allow_notifications.return_value = False

        subscribers.send_mention_notifications(event)

        tasks_mailer.send.delay.assert_not_called()

    @pytest.fixture
    def event(self, pyramid_request):
        return AnnotationEvent(pyramid_request, {"id": "any"}, "action")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.tm = mock.MagicMock()
        return pyramid_request


class TestSyncAnnotation:
    def test_it_calls_sync_service(
        self, pyramid_request, search_index, transaction_manager
    ):
        event = AnnotationEvent(pyramid_request, {"id": "any"}, "action")

        subscribers.annotation_sync(event)

        transaction_manager.__enter__.assert_called_once()
        search_index.handle_annotation_event.assert_called_once_with(event)
        transaction_manager.__exit__.assert_called_once()

    @pytest.fixture
    def transaction_manager(self, pyramid_request):
        pyramid_request.tm = mock.create_autospec(
            TransactionManager, instance=True, spec_set=True
        )
        return pyramid_request.tm


class TestPublishAnnotationEventForAuthority:
    def test_it(self, pyramid_request, annotations):
        event = AnnotationEvent(pyramid_request, {"id": "any"}, "action")

        subscribers.publish_annotation_event_for_authority(event)

        annotations.publish_annotation_event_for_authority.delay.assert_called_once_with(
            event.action, event.annotation_id
        )


@pytest.fixture(autouse=True)
def reply(patch):
    return patch("h.subscribers.reply")


@pytest.fixture(autouse=True)
def mention(patch):
    mention = patch("h.subscribers.mention")
    mention.get_notifications.return_value = [mock.MagicMock()]
    return mention


@pytest.fixture(autouse=True)
def tasks_mailer(patch):
    mock = patch("h.subscribers.mailer")
    mock.send.delay = create_autospec(mailer.send.run)
    return mock


@pytest.fixture(autouse=True)
def annotations(patch):
    return patch("h.subscribers.annotations")


@pytest.fixture(autouse=True)
def emails(patch):
    return patch("h.subscribers.emails")


@pytest.fixture(autouse=True)
def report_exception(patch):
    return patch("h.subscribers.report_exception")


@pytest.fixture(autouse=True)
def asdict(patch):
    return patch(
        "h.subscribers.asdict", side_effect=[sentinel.email_data, sentinel.log_data]
    )


@pytest.fixture(autouse=True)
def LogData(patch):
    return patch("h.subscribers.LogData", autospec=True)
