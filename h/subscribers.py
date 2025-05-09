import logging
from dataclasses import asdict

from h_pyramid_sentry import report_exception
from kombu.exceptions import OperationalError
from pyramid.events import BeforeRender, subscriber

from h import __version__, emails
from h.events import AnnotationEvent
from h.exceptions import RealtimeMessageQueueError
from h.models.notification import NotificationType
from h.notification import mention, reply
from h.services import NotificationService
from h.services.annotation_read import AnnotationReadService
from h.services.email import TaskData
from h.tasks import annotations, email

logger = logging.getLogger(__name__)


@subscriber(BeforeRender)
def add_renderer_globals(event):
    request = event["request"]

    event["base_url"] = request.route_url("index")
    event["feature"] = request.feature

    event["google_analytics_measurement_id"] = request.registry.settings.get(
        "google_analytics_measurement_id"
    )

    # Add a frontend settings object which will be rendered as JSON into the
    # page.
    event["frontend_settings"] = {}

    if "h.sentry_dsn_frontend" in request.registry.settings:
        event["frontend_settings"]["sentry"] = {
            "dsn": request.registry.settings["h.sentry_dsn_frontend"],
            "environment": request.registry.settings["h.sentry_environment"],
            "release": __version__,
            "userid": request.authenticated_userid,
        }


# The docs say the order isn't guaranteed but pyramid appears to execute the
# subscribers in alphabetical order. We'd like the annotation_sync() event
# first, as it's the most important. If # we have Celery problems, we don't
# want to wait behind other tasks resolving it.


@subscriber(AnnotationEvent)
def annotation_sync(event):
    """Ensure an annotation is synchronised to Elasticsearch."""

    # Checking feature flags opens a connection to the database. As this event
    # is processed after the main transaction has closed, we must open a new
    # transaction to ensure we don't leave an un-closed transaction
    with event.request.tm:
        search_index = event.request.find_service(name="search_index")
        search_index.handle_annotation_event(event)


@subscriber(AnnotationEvent)
def publish_annotation_event(event):
    """Publish an annotation event to the message queue."""
    data = {
        "action": event.action,
        "annotation_id": event.annotation_id,
        "src_client_id": event.request.headers.get("X-Client-Id"),
    }
    try:
        event.request.realtime.publish_annotation(data)

    except RealtimeMessageQueueError as err:
        report_exception(err)


@subscriber(AnnotationEvent)
def send_reply_notifications(event) -> None:
    """Queue any reply notification emails triggered by an annotation event."""
    request = event.request

    notification_service: NotificationService = request.find_service(
        NotificationService
    )

    with request.tm:
        annotation = request.find_service(AnnotationReadService).get_annotation_by_id(
            event.annotation_id
        )

        notification = reply.get_notification(request, annotation, event.action)
        if notification is None:
            return

        # Don't send a notification to users already mentioned in the reply
        mentioned_users = {
            notification.mentioned_user
            for notification in mention.get_notifications(
                request, annotation, event.action
            )
        }
        if notification.parent_user in mentioned_users:
            return

        if not notification_service.allow_notifications(
            annotation, notification.parent_user
        ):
            logger.info("Skipping reply notification for %s", notification.parent_user)
            return

        email_data = emails.reply_notification.generate(request, notification)
        task_data = TaskData(
            tag=email_data.tag,
            sender_id=notification.reply_user.id,
            recipient_ids=[notification.parent_user.id],
            extra={"annotation_id": annotation.id},
        )
        try:
            email.send.delay(asdict(email_data), asdict(task_data))
        except OperationalError as err:  # pragma: no cover
            # We could not connect to rabbit! So carry on
            report_exception(err)

        notification_service.save_notification(
            annotation=annotation,
            recipient=notification.parent_user,
            notification_type=NotificationType.REPLY,
        )


@subscriber(AnnotationEvent)
def send_mention_notifications(event) -> None:
    """Send mention notifications triggered by a mention event."""
    request = event.request

    notification_service: NotificationService = request.find_service(
        NotificationService
    )

    with request.tm:
        annotation = request.find_service(AnnotationReadService).get_annotation_by_id(
            event.annotation_id,
        )

        notifications = mention.get_notifications(request, annotation, event.action)
        for notification in notifications:
            if not notification_service.allow_notifications(
                annotation, notification.mentioned_user
            ):
                logger.info(
                    "Skipping mention notification for %s", notification.mentioned_user
                )
                continue

            email_data = emails.mention_notification.generate(request, notification)
            task_data = TaskData(
                tag=email_data.tag,
                sender_id=notification.mentioning_user.id,
                recipient_ids=[notification.mentioned_user.id],
                extra={"annotation_id": annotation.id},
            )
            try:
                email.send.delay(asdict(email_data), asdict(task_data))
            except OperationalError as err:  # pragma: no cover
                # We could not connect to rabbit! So carry on
                report_exception(err)

            notification_service.save_notification(
                annotation=annotation,
                recipient=notification.mentioned_user,
                notification_type=NotificationType.MENTION,
            )


@subscriber(AnnotationEvent)
def publish_annotation_event_for_authority(event):
    annotations.publish_annotation_event_for_authority.delay(
        event.action, event.annotation_id
    )
