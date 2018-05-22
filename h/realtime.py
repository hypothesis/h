# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import base64
import random
import struct
from datetime import datetime

import kombu
from kombu.mixins import ConsumerMixin
from kombu.pools import producers as producer_pool


class Consumer(ConsumerMixin):
    """
    A realtime consumer that listens to the configured routing key and calls
    the wrapped handler function on receiving a matching message.

    Conforms to the :py:class:`kombu.mixins.ConsumerMixin` interface.

    :param connection: a `kombe.Connection`
    :param routing_key: listen to messages with this routing key
    :param handler: the function which gets called when a messages arrives
    :param sentry_client: an optional Sentry client for error reporting
    """

    def __init__(self,
                 connection,
                 routing_key,
                 handler,
                 sentry_client=None,
                 statsd_client=None):
        self.connection = connection
        self.routing_key = routing_key
        self.handler = handler
        self.exchange = get_exchange()
        self.sentry_client = sentry_client
        self.statsd_client = statsd_client

    def get_consumers(self, consumer_factory, channel):
        name = self.generate_queue_name()
        queue = kombu.Queue(name, self.exchange,
                            durable=False,
                            routing_key=self.routing_key,
                            auto_delete=True)
        return [consumer_factory(queues=[queue], callbacks=[self.handle_message])]

    def generate_queue_name(self):
        return 'realtime-{}-{}'.format(self.routing_key, self._random_id())

    def handle_message(self, body, message):
        """
        Handles a realtime message by acknowledging it and then calling the
        wrapped handler.
        """
        if self.statsd_client:
            self._record_time_in_queue(message)
        message.ack()
        self.handler(body)

    def on_connection_error(self, exc, interval):
        if self.sentry_client:
            extra = {'exchange': self.exchange.name}
            self.sentry_client.captureException(extra=extra)

        super(Consumer, self).on_connection_error(exc, interval)

    def on_decode_error(self, message, exc):
        if self.sentry_client:
            extra = {'exchange': self.exchange.name,
                     'message_headers': message.headers,
                     'message_properties': message.properties}
            self.sentry_client.captureException(extra=extra)

        super(Consumer, self).on_decode_error(message, exc)

    def _random_id(self):
        """Generate a short random string"""
        data = struct.pack('Q', random.getrandbits(64))
        return base64.urlsafe_b64encode(data).strip(b'=')

    def _record_time_in_queue(self, message):
        """Send a very rough estimate of time-in-queue to the stats client."""
        # N.B. This gives only a *rough approximation* of the time spent in the
        # message queue. Using wall clocks like this is NOT going to be very
        # accurate.
        if 'timestamp' not in message.headers:
            return

        timestamp = datetime.strptime(message.headers['timestamp'],
                                      '%Y-%m-%dT%H:%M:%S.%fZ')
        delta = datetime.utcnow() - timestamp
        delta_millis = int(delta.total_seconds() * 1000)

        self.statsd_client.timing('streamer.msg.queueing', delta_millis)


class Publisher(object):
    """
    A realtime publisher for publishing messages to all subscribers.

    An instance of this publisher is available on Pyramid requests
    with `request.realtime`.

    :param request: a `pyramid.request.Request`
    """
    def __init__(self, request):
        self.connection = get_connection(request.registry.settings)
        self.exchange = get_exchange()

    def publish_annotation(self, payload):
        """Publish an annotation message with the routing key 'annotation'."""
        self._publish('annotation', payload)

    def publish_user(self, payload):
        """Publish a user message with the routing key 'user'."""
        self._publish('user', payload)

    def _publish(self, routing_key, payload):
        headers = {'timestamp': datetime.utcnow().isoformat() + 'Z'}

        with producer_pool[self.connection].acquire(block=True) as producer:
            producer.publish(payload,
                             exchange=self.exchange,
                             declare=[self.exchange],
                             routing_key=routing_key,
                             headers=headers)


class DummyPublisher(object):
    """
    A dummy implementation of `Publisher` used when realtime support is disabled.
    """
    def __init__(self, request):
        pass

    def publish_annotation(self, payload):
        pass

    def publish_user(self, payload):
        pass


def get_exchange():
    """Returns a configures `kombu.Exchange` to use for realtime messages."""

    return kombu.Exchange('realtime',
                          type='direct',
                          durable=False,
                          delivery_mode='transient')


def get_connection(settings):
    """Returns a `kombu.Connection` based on the application's settings."""

    conn = settings.get('broker_url', 'amqp://guest:guest@localhost:5672//')
    return kombu.Connection(conn)


def includeme(config):
    broker_url = config.registry.get('broker_url', '')
    if broker_url.startswith('sqs://'):
        # The realtime API relies on multicast delivery of each message from
        # a web process to all running websocket server processes.
        #
        # This is not supported when using Amazon SQS as the messaging backend.
        config.add_request_method(DummyPublisher, name='realtime', reify=True)
    else:
        config.add_request_method(Publisher, name='realtime', reify=True)
