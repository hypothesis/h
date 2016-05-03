# -*- coding: utf-8 -*-

from h import __version__
from h import emails
from h import mailer
from h.api import presenters
from h.notification import reply


def add_renderer_globals(event):
    request = event['request']

    event['h_version'] = __version__
    event['base_url'] = request.route_url('index')
    event['feature'] = request.feature

    # Add Google Analytics
    ga_tracking_id = request.registry.settings.get('ga_tracking_id')
    if ga_tracking_id is not None:
        event['ga_tracking_id'] = ga_tracking_id
        if 'localhost' in request.host:
            event['ga_cookie_domain'] = "none"
        else:
            event['ga_cookie_domain'] = "auto"


def publish_annotation_event(event):
    """Publish an annotation event to the message queue."""
    annotation_dict = presenters.AnnotationJSONPresenter(
        event.request, event.annotation).asdict()

    data = {
        'action': event.action,
        'annotation': annotation_dict,
        'src_client_id': event.request.headers.get('X-Client-Id'),
    }

    event.request.realtime.publish_annotation(data)


def send_reply_notifications(event,
                             get_notification=reply.get_notification,
                             generate_mail=emails.reply_notification.generate,
                             send=mailer.send.delay):
    """Queue any reply notification emails triggered by an annotation event."""
    request = event.request
    annotation = event.annotation
    action = event.action
    try:
        notification = get_notification(request, annotation, action)
        if notification is None:
            return
        send_params = generate_mail(request, notification)
        send(*send_params)
    # We don't want any exceptions thrown by this code to cause the annotation
    # CRUD action to fail, but we do want to collect the error in Sentry, so we
    # explicitly wrap this here.
    #
    # FIXME: Fix the underlying bugs and remove this try/except.
    except Exception:
        event.request.sentry.captureException()
        if event.request.debug:
            raise
