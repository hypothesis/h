import collections
import logging

from h_pyramid_sentry import report_exception
from zope.interface import providedBy

log = logging.getLogger(__name__)


def _get_subscribers(registry, event):
    # This code is adapted from the `subscribers` method in
    # `zope.interface.adapter` which is what Pyramid's `request.registry.notify`
    # is a very thin wrapper around.
    return registry.adapters.subscriptions([providedBy(event)], None)


class EventQueue:
    """
    EventQueue enables dispatching Pyramid events at the end of a request.

    An instance of this class is exposed on the request object via the
    `notify_after_commit` method. The `_after_commit` part refers to the
    database transaction associated with the request. Unlike calling
    `request.registry.notify` during a request, failures will not cause a
    database transaction rollback.

    Events are dispatched in the order they are queued. Failure of one
    event subscriber does not affect execution of other subscribers.
    """

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
                except Exception:  # pylint: disable=broad-except
                    if event.request.debug:
                        raise
                    report_exception()

    def response_callback(self, request, _response):
        if request.exception is not None:
            return

        self.publish_all()


def includeme(config):  # pragma: nocover
    config.add_request_method(EventQueue, name="notify_after_commit", reify=True)
