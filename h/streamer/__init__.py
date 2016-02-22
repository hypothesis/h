# -*- coding: utf-8 -*-

import gevent

from h.streamer import nsq


def start_streamer(event):
    """
    Start some greenlets to process the incoming data from NSQ.

    This subscriber is called when the application is booted, and kicks off
    greenlets running `process_queue` for each NSQ topic we subscribe to. The
    function does not block.
    """
    def _loop(settings, topic, handler):
        while True:
            nsq.process_queue(settings, topic, handler)

    settings = event.app.registry.settings
    gevent.spawn(_loop, settings, nsq.ANNOTATIONS_TOPIC, nsq.handle_annotation_event)
    gevent.spawn(_loop, settings, nsq.USER_TOPIC, nsq.handle_user_event)


def includeme(config):
    config.include('h.streamer.views')

    config.add_route('ws', 'ws')
    config.add_subscriber(start_streamer, 'pyramid.events.ApplicationCreated')
