from h import __version__, emails, storage
from h.notification import reply
from h.tasks import mailer
from h.tasks.indexer import add_annotation, delete_annotation


def includeme(config):
    config.add_subscriber(
        "h.subscribers.add_renderer_globals", "pyramid.events.BeforeRender"
    )
    config.add_subscriber(
        "h.subscribers.publish_annotation_event", "h.events.AnnotationEvent"
    )
    config.add_subscriber(
        "h.subscribers.send_reply_notifications", "h.events.AnnotationEvent"
    )
    # Register the transform_annotation subscriber so that nipsa fields are
    # written into annotations on save.
    config.add_subscriber(
        "h.subscribers.nipsa_transform_annotation", "h.events.AnnotationTransformEvent",
    )

    config.add_subscriber(
        "h.subscribers.subscribe_annotation_event", "h.events.AnnotationEvent"
    )


def add_renderer_globals(event):
    request = event["request"]

    event["base_url"] = request.route_url("index")
    event["feature"] = request.feature

    # Add Google Analytics
    event["ga_tracking_id"] = request.registry.settings.get("ga_tracking_id")

    # Add a frontend settings object which will be rendered as JSON into the
    # page.
    event["frontend_settings"] = {}

    if "h.sentry_dsn_frontend" in request.registry.settings:
        event["frontend_settings"]["raven"] = {
            "dsn": request.registry.settings["h.sentry_dsn_frontend"],
            "release": __version__,
            "userid": request.authenticated_userid,
        }


def publish_annotation_event(event):
    """Publish an annotation event to the message queue."""
    data = {
        "action": event.action,
        "annotation_id": event.annotation_id,
        "src_client_id": event.request.headers.get("X-Client-Id"),
    }
    event.request.realtime.publish_annotation(data)


def send_reply_notifications(
    event,
    get_notification=reply.get_notification,
    generate_mail=emails.reply_notification.generate,
    send=mailer.send.delay,
):
    """Queue any reply notification emails triggered by an annotation event."""
    request = event.request
    with request.tm:
        annotation = storage.fetch_annotation(event.request.db, event.annotation_id)
        notification = get_notification(request, annotation, event.action)
        if notification is None:
            return

        send_params = generate_mail(request, notification)
        send(*send_params)


def nipsa_transform_annotation(event):
    """Mark moderated or flagged annotations.

    Adds `{"nipsa": True}` to an annotation.
    """
    user = event.annotation_dict.get("user")
    if user is None:
        return

    nipsa_service = event.request.find_service(name="nipsa")
    if nipsa_service.is_flagged(user):
        event.annotation_dict["nipsa"] = True


def sync_annotation(event):
    """Ensure an annotation is synchronised to Elasticsearch."""

    if event.action in ["create", "update"]:
        add_annotation.delay(event.annotation_id)

    elif event.action == "delete":
        delete_annotation.delay(event.annotation_id)
