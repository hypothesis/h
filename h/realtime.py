import base64
import random
import struct

import kombu
from kombu.exceptions import LimitExceeded, OperationalError
from kombu.mixins import ConsumerMixin
from kombu.pools import producers as producer_pool

from h.exceptions import RealtimeMessageQueueError
from h.tasks import RETRY_POLICY_QUICK, RETRY_POLICY_VERY_QUICK


class Consumer(ConsumerMixin):
    """
    A realtime consumer.

    Listens to the configured routing key and calls
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

    def get_consumers(
        self, consumer_factory, channel
    ):  # pylint: disable=arguments-renamed
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
        return f"realtime-{self.routing_key}-{self._random_id()}"

    def handle_message(self, body, message):
        """Handle a realtime message by acknowledging it and then calling the wrapped handler."""
        message.ack()
        self.handler(body)

    @staticmethod
    def _random_id():
        """Generate a short random string."""
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
        self.connection = get_connection(request.registry.settings, fail_fast=True)
        self.exchange = get_exchange()

    def publish_annotation(self, payload):
        """
        Publish an annotation message with the routing key 'annotation'.

        :raise RealtimeMessageQueueError: When we cannot queue the message
        """
        self._publish("annotation", payload)

    def publish_user(self, payload):
        """
        Publish a user message with the routing key 'user'.

        :raise RealtimeMessageQueueError: When we cannot queue the message
        """
        self._publish("user", payload)

    def _publish(self, routing_key, payload):
        try:  # pylint: disable=too-many-try-statements
            with producer_pool[self.connection].acquire(
                block=True, timeout=1
            ) as producer:
                producer.publish(
                    payload,
                    exchange=self.exchange,
                    declare=[self.exchange],
                    routing_key=routing_key,
                    retry=True,
                    # This is the retry for the producer, the connection
                    # retry is separate
                    retry_policy=RETRY_POLICY_VERY_QUICK,
                )

        except (OperationalError, LimitExceeded) as err:
            # If we fail to connect (OperationalError), or we don't get a
            # producer from the pool in time (LimitExceeded) raise
            raise RealtimeMessageQueueError() from err


def get_exchange():
    """Get a configured `kombu.Exchange` to use for realtime messages."""

    return kombu.Exchange(
        "realtime", type="direct", durable=False, delivery_mode="transient"
    )


def get_connection(settings, fail_fast=False):
    """
    Return a `kombu.Connection` based on the application's settings.

    :param settings: Application settings
    :param fail_fast: Make the connection fail if we cannot get a connection
        quickly.
    """

    conn = settings.get("broker_url", "amqp://guest:guest@localhost:5672//")

    kwargs = {}
    if fail_fast:
        # Connection fallback set by`kombu.connection._extract_failover_opts`
        # Which are used when retrying a connection as sort of documented here:
        # https://kombu.readthedocs.io/en/latest/reference/kombu.connection.html#kombu.connection.Connection.ensure_connection
        # Maximum number of times to retry. If this limit is exceeded the
        # connection error will be re-raised.
        kwargs["transport_options"] = RETRY_POLICY_QUICK

    return kombu.Connection(conn, **kwargs)


def includeme(config):  # pragma: nocover
    config.add_request_method(Publisher, name="realtime", reify=True)
