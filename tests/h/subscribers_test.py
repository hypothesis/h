from unittest import mock

import pytest

from h import subscribers
from h.events import AnnotationEvent


class FakeMailer:
    def __init__(self):
        self.lastcall = None

    def __call__(self, recipients, subject, body, html):
        self.lastcall = (recipients, subject, body, html)


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

    @pytest.fixture
    def event(self, pyramid_request):
        pyramid_request.realtime = mock.Mock()
        event = AnnotationEvent(pyramid_request, "test_annotation_id", "create")
        return event


@pytest.mark.usefixtures("fetch_annotation")
class TestSendReplyNotifications:
    def test_calls_get_notification_with_request_annotation_and_action(
        self, fetch_annotation, pyramid_request
    ):
        send = FakeMailer()
        get_notification = mock.Mock(spec_set=[], return_value=None)
        generate_mail = mock.Mock(spec_set=[], return_value=[])
        event = AnnotationEvent(
            pyramid_request, mock.sentinel.annotation_id, mock.sentinel.action
        )

        subscribers.send_reply_notifications(
            event,
            get_notification=get_notification,
            generate_mail=generate_mail,
            send=send,
        )

        fetch_annotation.assert_called_once_with(
            pyramid_request.db, mock.sentinel.annotation_id
        )

        get_notification.assert_called_once_with(
            pyramid_request, fetch_annotation.return_value, mock.sentinel.action
        )

    def test_generates_and_sends_mail_for_any_notification(self, pyramid_request):
        send = FakeMailer()
        get_notification = mock.Mock(
            spec_set=[], return_value=mock.sentinel.notification
        )
        generate_mail = mock.Mock(spec_set=[])
        generate_mail.return_value = (
            ["foo@example.com"],
            "Your email",
            "Text body",
            "HTML body",
        )
        event = AnnotationEvent(pyramid_request, None, None)

        subscribers.send_reply_notifications(
            event,
            get_notification=get_notification,
            generate_mail=generate_mail,
            send=send,
        )

        generate_mail.assert_called_once_with(
            pyramid_request, mock.sentinel.notification
        )
        assert send.lastcall == (
            ["foo@example.com"],
            "Your email",
            "Text body",
            "HTML body",
        )

    @pytest.fixture
    def fetch_annotation(self, patch):
        return patch("h.subscribers.storage.fetch_annotation")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.tm = mock.MagicMock()
        return pyramid_request


class TestSyncAnnotation:
    @pytest.mark.usefixtures("without_synchronous_flag")
    @pytest.mark.parametrize("action", ["create", "update"])
    def test_it_enqueues_add_annotation_celery_task(
        self, pyramid_request, action, add_annotation, delete_annotation
    ):
        event = AnnotationEvent(pyramid_request, {"id": "any"}, action)

        subscribers.sync_annotation(event)

        add_annotation.delay.assert_called_once_with(event.annotation_id)
        assert not delete_annotation.delay.called

    @pytest.mark.usefixtures("without_synchronous_flag")
    def test_it_enqueues_delete_annotation_celery_task_for_delete(
        self, add_annotation, delete_annotation, pyramid_request
    ):
        event = AnnotationEvent(pyramid_request, {"id": "test_annotation_id"}, "delete")

        subscribers.sync_annotation(event)

        delete_annotation.delay.assert_called_once_with(event.annotation_id)
        assert not add_annotation.delay.called

    @pytest.mark.parametrize(
        "action,method",
        (
            ("create", "add_annotation_by_id"),
            ("update", "add_annotation_by_id"),
            ("delete", "delete_annotation_by_id"),
        ),
    )
    @pytest.mark.usefixtures("with_synchronous_flag")
    def test_it_calls_sync_service(
        self, action, pyramid_request, search_index, method, transaction_manager
    ):
        event = AnnotationEvent(pyramid_request, {"id": "any"}, action)

        subscribers.sync_annotation(event)

        transaction_manager.__enter__.assert_called_once()
        getattr(search_index, method).assert_called_once_with(event.annotation_id)
        transaction_manager.__exit__.assert_called_once()

    @pytest.fixture(autouse=True)
    def transaction_manager(self, pyramid_request):
        pyramid_request.tm = mock.MagicMock(spec=["__enter__", "__exit__"])
        return pyramid_request.tm

    @pytest.fixture
    def with_synchronous_flag(self, pyramid_request):
        pyramid_request.feature.flags = {"synchronous_indexing": True}

    @pytest.fixture
    def without_synchronous_flag(self, pyramid_request):
        pyramid_request.feature.flags = {"synchronous_indexing": False}

    @pytest.fixture(autouse=True)
    def add_annotation(self, patch):
        return patch("h.subscribers.add_annotation")

    @pytest.fixture(autouse=True)
    def delete_annotation(self, patch):
        return patch("h.subscribers.delete_annotation")
