from unittest import mock

import kombu
import pytest
from h_matchers import Any
from kombu.exceptions import LimitExceeded, OperationalError

from h import realtime
from h.exceptions import RealtimeMessageQueueError
from h.tasks import RETRY_POLICY_QUICK, RETRY_POLICY_VERY_QUICK


class TestConsumer:
    def test_init_stores_connection(self, consumer):
        assert consumer.connection == mock.sentinel.connection

    def test_init_stores_routing_key(self, consumer):
        assert consumer.routing_key == "annotation"

    def test_init_stores_handler(self, consumer, handler):
        assert consumer.handler == handler

    def test_get_consumers_creates_a_queue(self, Queue, consumer, generate_queue_name):
        consumer_factory = mock.Mock(spec_set=[])
        exchange = realtime.get_exchange()

        consumer.get_consumers(consumer_factory, mock.Mock())

        Queue.assert_called_once_with(
            generate_queue_name.return_value,
            exchange=exchange,
            durable=False,
            routing_key="annotation",
            auto_delete=True,
        )

    def test_get_consumers_creates_a_consumer(self, Queue, consumer):
        consumer_factory = mock.Mock(spec_set=[])
        consumer.get_consumers(consumer_factory, channel=None)
        consumer_factory.assert_called_once_with(
            queues=[Queue.return_value], callbacks=[consumer.handle_message]
        )

    def test_get_consumers_returns_list_of_one_consumer(self, consumer):
        consumer_factory = mock.Mock(spec_set=[])
        consumers = consumer.get_consumers(consumer_factory, channel=None)
        assert consumers == [consumer_factory.return_value]

    def test_handle_message_acks_message(self, consumer):
        message = mock.Mock()
        consumer.handle_message({}, message)

        message.ack.assert_called_once_with()

    def test_handle_message_calls_the_handler(self, consumer, handler):
        body = {"foo": "bar"}
        consumer.handle_message(body, mock.Mock())

        handler.assert_called_once_with(body)

    def test_handle_message_doesnt_explode_if_timestamp_missing(self, handler):
        consumer = realtime.Consumer(mock.sentinel.connection, "annotation", handler)
        message = mock.Mock()
        message.headers = {}

        consumer.handle_message({}, message)

    @pytest.fixture
    def Queue(self, patch):
        return patch("h.realtime.kombu.Queue")

    @pytest.fixture
    def consumer(self, handler):
        return realtime.Consumer(mock.sentinel.connection, "annotation", handler)

    @pytest.fixture
    def handler(self):
        return mock.Mock(spec_set=[])

    @pytest.fixture
    def generate_queue_name(self, patch):
        return patch("h.realtime.Consumer.generate_queue_name")


class TestPublisher:
    def test_publish_annotation(self, producer, publisher, exchange):
        payload = {"action": "create", "annotation": {"id": "foobar"}}

        publisher.publish_annotation(payload)

        producer.publish.assert_called_once_with(
            payload,
            exchange=exchange,
            declare=[exchange],
            routing_key="annotation",
            retry=True,
            retry_policy=RETRY_POLICY_VERY_QUICK,
        )

    def test_publish_user(self, producer, publisher, exchange):
        payload = {"action": "create", "user": {"id": "foobar"}}

        publisher.publish_user(payload)

        producer.publish.assert_called_once_with(
            payload,
            exchange=exchange,
            declare=[exchange],
            routing_key="user",
            retry=True,
            retry_policy=RETRY_POLICY_VERY_QUICK,
        )

    @pytest.mark.parametrize("exception", (OperationalError, LimitExceeded))
    def test_it_raises_RealtimeMessageQueueError_on_errors(
        self, publisher, producer, exception
    ):
        producer.publish.side_effect = exception

        with pytest.raises(RealtimeMessageQueueError):
            publisher.publish_user({})

    @pytest.fixture
    def producer(self, patch):
        producer_pool = patch("h.realtime.producer_pool")
        with producer_pool["foobar"].acquire() as pool:
            yield pool

    @pytest.fixture
    def publisher(self, pyramid_request):
        return realtime.Publisher(pyramid_request)

    @pytest.fixture
    def exchange(self):
        return realtime.get_exchange()


class TestGetExchange:
    def test_returns_the_exchange(self):
        exchange = realtime.get_exchange()
        assert isinstance(exchange, kombu.Exchange)

    def test_type(self):
        exchange = realtime.get_exchange()
        assert exchange.type == "direct"

    def test_durable(self):
        exchange = realtime.get_exchange()
        assert not exchange.durable

    def test_delivery_mode(self):
        """Test that delivery mode is 1 (transient)."""
        exchange = realtime.get_exchange()
        assert exchange.delivery_mode == 1


class TestGetConnection:
    def test_defaults(self, Connection):
        realtime.get_connection({})
        Connection.assert_called_once_with("amqp://guest:guest@localhost:5672//")

    def test_returns_the_connection(self, Connection):
        connection = realtime.get_connection({})
        assert connection == Connection.return_value

    def test_allows_to_overwrite_broker_url(self, Connection):
        broker_url = "amqp://alice:bob@rabbitmq.int:5673/prj"
        realtime.get_connection({"broker_url": broker_url})
        Connection.assert_called_once_with(broker_url)

    def test_it_adds_timeout_options_for_failfast(self, Connection):
        realtime.get_connection({}, fail_fast=True)

        Connection.assert_called_once_with(
            Any.string(), transport_options=RETRY_POLICY_QUICK
        )

    @pytest.fixture
    def Connection(self, patch):
        return patch("h.realtime.kombu.Connection")
