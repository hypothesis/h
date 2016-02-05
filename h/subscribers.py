# -*- coding: utf-8 -*-

import json

from h import __version__


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
    queue = event.request.get_queue_writer()
    data = {
        'action': event.action,
        'annotation': event.annotation,
        'src_client_id': event.request.headers.get('X-Client-Id'),
    }
    queue.publish('annotations', json.dumps(data))
