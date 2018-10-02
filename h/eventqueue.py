# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import collections
import logging

from zope.interface import providedBy


log = logging.getLogger(__name__)


def _get_subscribers(registry, event):
    # This code is adapted from the `subscribers` method in
    # `zope.interface.adapter` which is what Pyramid's `request.registry.notify`
    # is a very thin wrapper around.
    return registry.adapters.subscriptions(map(providedBy, [event]), None)


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

            # Get subscribers to event and invoke them. The normal way to do
            # this in Pyramid is to invoke `registry.notify`, but that provides
            # no guarantee about the order of execution and any failure causes
            # later subscribers not to run.
            #
            # Here we wrap each subscriber call in an exception handler to
            # make failure independent in non-debug environments.
            subscribers = _get_subscribers(self.request.registry, event)
            for subscriber in subscribers:
                try:
                    subscriber(event)
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
