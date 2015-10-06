# -*- coding: utf-8 -*-
"""Publish events into the distributed message queue."""
import json

from h.api.events import Event, AnnotationEvent, UserStatusEvent

def publish_event(event):
    # We only publish these events to NSQ if the 'queue' feature is enabled.
    if not event.request.feature('queue'):
        return

    if isinstance(event, AnnotationEvent):
        publish_annotation_event(event)
    elif isinstance(event, UserStatusEvent):
        publish_user_event(event)

def publish_annotation_event(event):
    """Publish an annotation event in NSQ."""
    request = event.request
    annotation = event.annotation
    action = event.action

    queue = request.get_queue_writer()
    data = {
        'action': action,
        'annotation': annotation,
        'src_client_id': request.headers.get('X-Client-Id'),
    }
    queue.publish('annotations', json.dumps(data))

def publish_user_event(event):
    """Publish a user status event in NSQ."""
    queue = event.request.get_queue_writer()
    data = {
        'user_id': event.user_id,
        'type': event.type,
        'group_id': event.group_id
    }
    queue.publish('user', json.dumps(data))

def includeme(config):
    config.include('h.queue')
    config.add_subscriber(publish_event, Event)
