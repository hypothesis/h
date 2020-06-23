# -*- coding: utf-8 -*-

import base64
import random
import struct

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
    """

    def __init__(self, connection, routing_key, handler):
        self.connection = connection
        self.routing_key = routing_key
        self.handler = handler
        self.exchange = get_exchange()

    def get_consumers(self, consumer_factory, channel):
        name = self.generate_queue_name()
        queue = kombu.Queue(
            name,
            self.exchange,
            durable=False,
            routing_key=self.routing_key,
            auto_delete=True,
        )
        return [consumer_factory(queues=[queue], callbacks=[self.handle_message])]

    def generate_queue_name(self):
        return "realtime-{}-{}".format(self.routing_key, self._random_id())

    def handle_message(self, body, message):
        """
        Handles a realtime message by acknowledging it and then calling the
        wrapped handler.
        """
        message.ack()
        self.handler(body)

    def _random_id(self):
        """Generate a short random string"""
        data = struct.pack("Q", random.getrandbits(64))
        return base64.urlsafe_b64encode(data).strip(b"=")


class Publisher:
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
        self._publish("annotation", payload)

    def publish_user(self, payload):
        """Publish a user message with the routing key 'user'."""
        self._publish("user", payload)

    def _publish(self, routing_key, payload):
        retry_policy = {"max_retries": 5, "interval_start": 0.2, "interval_step": 0.3}

        with producer_pool[self.connection].acquire(block=True) as producer:
            producer.publish(
                payload,
                exchange=self.exchange,
                declare=[self.exchange],
                routing_key=routing_key,
                retry=True,
                retry_policy=retry_policy,
            )


def get_exchange():
    """Returns a configures `kombu.Exchange` to use for realtime messages."""

    return kombu.Exchange(
        "realtime", type="direct", durable=False, delivery_mode="transient"
    )


def get_connection(settings):
    """Returns a `kombu.Connection` based on the application's settings."""

    conn = settings.get("broker_url", "amqp://guest:guest@localhost:5672//")
    return kombu.Connection(conn)


def includeme(config):
    config.add_request_method(Publisher, name="realtime", reify=True)
