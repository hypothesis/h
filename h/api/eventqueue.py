# -*- coding: utf-8 -*-

import collections


class EventQueue(object):
    def __init__(self, request):
        self.request = request
        self.queue = collections.deque()

        request.add_response_callback(self.response_callback)

    def __call__(self, event):
        self.queue.append(event)

    def publish_all(self):
        while True:
            try:
                event = self.queue.popleft()
            except IndexError:
                break
            self.request.registry.notify(event)

    def response_callback(self, request, response):
        if request.exception is not None:
            return

        with request.tm:
            self.publish_all()


def includeme(config):
    config.add_request_method(EventQueue,
                              name='notify_after_commit',
                              reify=True)
