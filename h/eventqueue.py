# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import collections
import logging


log = logging.getLogger(__name__)


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

            try:
                # Notify all subscribers to this particular event. Note that the
                # order in which subcribers run is not guaranteed [1] and if one
                # fails, remaining subscribers to the same event which have not
                # yet run will be skipped.
                #
                # [1] See https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/events.html
                self.request.registry.notify(event)
            except Exception:
                sentry = getattr(event.request, 'sentry', None)
                if sentry is not None:
                    sentry.captureException()
                else:
                    log.exception('Queued event subscriber failed')

                if event.request.debug:
                    raise

    def response_callback(self, request, response):
        if request.exception is not None:
            return

        self.publish_all()


def includeme(config):
    config.add_request_method(EventQueue,
                              name='notify_after_commit',
                              reify=True)
