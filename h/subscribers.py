# -*- coding: utf-8 -*-


from __future__ import unicode_literals
from h import __version__
from h import emails
from h import storage
from h.notification import reply
from h.tasks import mailer


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
