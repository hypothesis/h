# -*- coding: utf-8 -*-
"""Publish annotations events into the distributed message queue."""
import json

from h.api.events import AnnotationEvent


def annotation(event):
    """Publish an annotation event in NSQ."""
    request = event.request
    annotation = event.annotation
    action = event.action

    # We only publish these events to NSQ if the 'queue' feature is enabled.
    if not request.feature('queue'):
        return

    queue = request.get_queue_writer()
    data = {
        'action': action,
        'annotation': annotation,
        'src_client_id': request.headers.get('X-Client-Id'),
    }
    queue.publish('annotations', json.dumps(data))


def includeme(config):
    config.include('h.queue')
    config.add_subscriber(annotation, AnnotationEvent)
