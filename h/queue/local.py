from collections import namedtuple
import logging

import blinker
import gevent
import gevent.queue
from pyramid.decorator import reify
from zope.interface import implementer

from . import interfaces

QUEUE_MAXSIZE = 1000
QUEUES = {}

log = logging.getLogger(__name__)


@implementer(interfaces.IQueueHelper)
class LocalQueueHelper(object):
    def __init__(self, settings):
        self.settings = settings

    def get_reader(self, topic, channel):
        """
        Get a :py:class:`h.queue.local.Reader` instance, providing access to a
        queue within the current thread. The reader will read from the
        specified topic and channel.

        The caller is responsible for adding appropriate `on_message` hooks and
        starting the reader.
        """
        return Reader(topic, channel)

    def get_writer(self):
        """
        Get a :py:class:`h.queue.local.Writer` instance, providing a mechanism
        to write to queues within the current thread.
        """
        return Writer()


class Reader(object):
    def __init__(self, topic, channel):
        """
        Create a new reader for the queue identified by the given topic.
        Channel is ignored, as there is no need for the channel concept within
        a thread. All subscribers to the on_message signal will receive
        messages.
        """
        self.topic = topic
        self.worker = None

    @reify
    def on_message(self):
        return blinker.Signal(doc='Emitted when a message is received.')

    def start(self, block=True):
        """
        Start processing the queue. Blocks until the queue is empty or closed
        if block is True.
        """
        if self.worker is not None:
            return
        queue = _get_queue(self.topic)
        self.worker = gevent.spawn(self._read_queue, queue)
        if block:
            self.join()

    def join(self, timeout=None):
        """Wait until the queue is empty or closed."""
        if self.worker is not None:
            self.worker.join(timeout)

    def close(self):
        """Stop reading from the queue"""
        if self.worker is not None:
            self.worker.kill()

    def _read_queue(self, queue):
        for message in queue:
            self.on_message.send(self, message=message)


class Writer(object):
    def publish(self, topic, body):
        """
        Publish a message with the given body to the queue identified by topic.
        """
        queue = _get_queue(topic)
        msg = Message(body)
        try:
            queue.put(msg)
        except gevent.queue.Full:
            log.warn("queue full, dropping message")


Message = namedtuple('Message', 'body')


def _get_queue(topic):
    try:
        queue = QUEUES[topic]
    except KeyError:
        queue = gevent.queue.Queue(maxsize=QUEUE_MAXSIZE)
        QUEUES[topic] = queue
    return queue


def includeme(config):
    registry = config.registry
    settings = registry.settings

    if not registry.queryUtility(interfaces.IQueueHelper):
        qh = LocalQueueHelper(settings)
        registry.registerUtility(qh, interfaces.IQueueHelper)
