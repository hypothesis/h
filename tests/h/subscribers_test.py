from unittest import mock

import pytest
from kombu.exceptions import OperationalError

from h import subscribers
from h.events import AnnotationEvent
from h.exceptions import RealtimeMessageQueueError


@pytest.mark.usefixtures("routes")
class TestAddRendererGlobals:
    def test_adds_base_url(self, event):
        subscribers.add_renderer_globals(event)

        assert event["base_url"] == "http://example.com/idx"

    def test_adds_feature_flag_client(self, event, pyramid_request):
        subscribers.add_renderer_globals(event)

        assert event["feature"] == pyramid_request.feature

    def test_adds_analytics_tracking_id(self, event, pyramid_request):
        pyramid_request.registry.settings["ga_tracking_id"] = "abcd1234"

        subscribers.add_renderer_globals(event)

        assert event["ga_tracking_id"] == "abcd1234"

    def test_adds_frontend_settings(self, event):
        subscribers.add_renderer_globals(event)

        assert event["frontend_settings"] == {}

    def test_adds_frontend_settings_raven(self, event, pyramid_request):
        settings = pyramid_request.registry.settings
        settings["h.sentry_dsn_frontend"] = "https://sentry.io/flibble"

        subscribers.add_renderer_globals(event)
        result = event["frontend_settings"]["raven"]

        assert result["dsn"] == "https://sentry.io/flibble"
        assert result["release"]
        assert result["userid"] is None

    def test_adds_frontend_settings_raven_user(
        self, event, pyramid_config, pyramid_request
    ):
        pyramid_config.testing_securitypolicy("acct:safet.baljić@example.com")
        settings = pyramid_request.registry.settings
        settings["h.sentry_dsn_frontend"] = "https://sentry.io/flibble"

        subscribers.add_renderer_globals(event)
        result = event["frontend_settings"]["raven"]["userid"]

        assert result == "acct:safet.baljić@example.com"

    @pytest.fixture
    def event(self, pyramid_request):
        return {"request": pyramid_request}

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("index", "/idx")


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

        with pytest.raises(EnvironmentError):
            subscribers.publish_annotation_event(event)

    @pytest.fixture
    def event(self, pyramid_request):
        pyramid_request.realtime = mock.Mock()
        event = AnnotationEvent(pyramid_request, "test_annotation_id", "create")
        return event


@pytest.mark.usefixtures("fetch_annotation")
class TestSendReplyNotifications:
    def test_it_sends_emails(
        self,
        event,
        pyramid_request,
        fetch_annotation,
        get_notification,
        reply_notification,
        mailer_task,
    ):

        subscribers.send_reply_notifications(event)

        # This is a pure plumbing test, checking everything is connected to
        # everything else as we expect
        fetch_annotation.assert_called_once_with(
            pyramid_request.db, event.annotation_id
        )
        annotation = fetch_annotation.return_value
        get_notification.assert_called_once_with(
            pyramid_request, annotation, event.action
        )
        notification = get_notification.return_value
        reply_notification.generate.assert_called_once_with(
            pyramid_request, notification
        )
        send_params = reply_notification.generate.return_value
        mailer_task.delay.assert_called_once_with(*send_params)

    def test_it_does_nothing_if_no_notification_is_required(
        self, event, get_notification, mailer_task
    ):
        get_notification.return_value = None

        subscribers.send_reply_notifications(event)

        mailer_task.delay.assert_not_called()

    def test_it_fails_gracefully_if_the_task_does_not_queue(self, event, mailer_task):
        mailer_task.side_effect = OperationalError

        # No explosions please
        subscribers.send_reply_notifications(event)

    @pytest.fixture
    def event(self, pyramid_request):
        return AnnotationEvent(pyramid_request, {"id": "any"}, "action")

    @pytest.fixture(autouse=True)
    def mailer_task(self, patch):
        return patch("h.subscribers.mailer.send")

    @pytest.fixture(autouse=True)
    def fetch_annotation(self, patch):
        return patch("h.subscribers.storage.fetch_annotation")

    @pytest.fixture(autouse=True)
    def get_notification(self, patch):
        return patch("h.subscribers.reply.get_notification")

    @pytest.fixture(autouse=True)
    def reply_notification(self, patch):
        return patch("h.subscribers.emails.reply_notification")

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
        from transaction import TransactionManager

        pyramid_request.tm = mock.create_autospec(
            TransactionManager, instance=True, spec_set=True
        )
        return pyramid_request.tm
