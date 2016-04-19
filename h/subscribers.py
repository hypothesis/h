# -*- coding: utf-8 -*-

import json

from h import __version__
from h import mailer
from h.api import presenters
from h.notification.reply_template import generate_notifications


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
                             generate=generate_notifications,
                             send=mailer.send.delay):
    """Queue any reply notification emails triggered by an annotation event."""
    try:
        notifications = generate(event.request, event.annotation, event.action)
        for (subject, body, html, recipients) in notifications:
            send(recipients, subject, body, html)
    # We know for a fact that occasionally `generate_notifications` throws
    # exceptions. We don't want this to cause the annotation CRUD action to
    # fail, but we do want to collect the error in Sentry, so we explicitly
    # wrap this here.
    #
    # FIXME: Fix the underlying bugs in `generate_notifications` and remove
    # this try/except.
    except Exception:
        event.request.sentry.captureException()
        if event.request.debug:
            raise
