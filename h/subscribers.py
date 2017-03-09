# -*- coding: utf-8 -*-


from h import __version__
from h import emails
from memex import storage
from h.notification import reply
from h.tasks import mailer


def add_renderer_globals(event):
    request = event['request']

    event['h_version'] = __version__
    event['base_url'] = request.route_url('index')
    event['feature'] = request.feature

    # Add Google Analytics
    event['ga_tracking_id'] = request.registry.settings.get('ga_tracking_id')


def publish_annotation_event(event):
    """Publish an annotation event to the message queue."""
    data = {
        'action': event.action,
        'annotation_id': event.annotation_id,
        'src_client_id': event.request.headers.get('X-Client-Id'),
    }
    event.request.realtime.publish_annotation(data)


def send_reply_notifications(event,
                             get_notification=reply.get_notification,
                             generate_mail=emails.reply_notification.generate,
                             send=mailer.send.delay):
    """Queue any reply notification emails triggered by an annotation event."""
    request = event.request
    with request.tm:
        annotation = storage.fetch_annotation(event.request.db,
                                              event.annotation_id)
        notification = get_notification(request, annotation, event.action)
        if notification is None:
            return
        send_params = generate_mail(request, notification)
        send(*send_params)
