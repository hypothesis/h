# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from datetime import datetime

import pytest
import mock

from h import realtime


class TestConsumer(object):
    def test_init_stores_connection(self, consumer):
        assert consumer.connection == mock.sentinel.connection

    def test_init_stores_routing_key(self, consumer):
        assert consumer.routing_key == 'annotation'

    def test_init_stores_handler(self, consumer, handler):
        assert consumer.handler == handler

    def test_get_consumers_creates_a_queue(self, Queue, consumer, generate_queue_name):
        consumer_factory = mock.Mock(spec_set=[])
        exchange = realtime.get_exchange()

        consumer.get_consumers(consumer_factory, mock.Mock())

        Queue.assert_called_once_with(generate_queue_name.return_value,
                                      exchange=exchange,
                                      durable=False,
                                      routing_key='annotation',
                                      auto_delete=True)

    def test_get_consumers_creates_a_consumer(self, Queue, consumer):
        consumer_factory = mock.Mock(spec_set=[])
        consumer.get_consumers(consumer_factory, channel=None)
        consumer_factory.assert_called_once_with(queues=[Queue.return_value],
                                                 callbacks=[consumer.handle_message])

    def test_get_consumers_returns_list_of_one_consumer(self, consumer):
        consumer_factory = mock.Mock(spec_set=[])
        consumers = consumer.get_consumers(consumer_factory, channel=None)
        assert consumers == [consumer_factory.return_value]

    def test_handle_message_acks_message(self, consumer):
        message = mock.Mock()
        consumer.handle_message({}, message)

        message.ack.assert_called_once_with()

    def test_handle_message_calls_the_handler(self, consumer, handler):
        body = {'foo': 'bar'}
        consumer.handle_message(body, mock.Mock())

        handler.assert_called_once_with(body)

    def test_handle_message_records_queue_time_if_timestamp_present(self, handler, matchers, statsd_client):
        consumer = realtime.Consumer(mock.sentinel.connection,
                                     'annotation',
                                     handler,
                                     statsd_client=statsd_client)
        message = mock.Mock()
        message.headers = {'timestamp': datetime.utcnow().isoformat() + 'Z'}

        consumer.handle_message({}, message)

        statsd_client.timing.assert_called_once_with('streamer.msg.queueing',
                                                     matchers.InstanceOf(int))

    def test_handle_message_doesnt_explode_if_timestamp_missing(self, handler, statsd_client):
        consumer = realtime.Consumer(mock.sentinel.connection,
                                     'annotation',
                                     handler,
                                     statsd_client=statsd_client)
        message = mock.Mock()
        message.headers = {}

        consumer.handle_message({}, message)

    @pytest.fixture
    def Queue(self, patch):
        return patch('h.realtime.kombu.Queue')

    @pytest.fixture
    def consumer(self, handler):
        return realtime.Consumer(mock.sentinel.connection, 'annotation', handler)

    @pytest.fixture
    def handler(self):
        return mock.Mock(spec_set=[])

    @pytest.fixture
    def statsd_client(self):
        return mock.Mock(spec_set=['timing'])

    @pytest.fixture
    def generate_queue_name(self, patch):
        return patch('h.realtime.Consumer.generate_queue_name')


class TestPublisher(object):
    def test_publish_annotation(self, matchers, producer_pool, pyramid_request):
        payload = {'action': 'create', 'annotation': {'id': 'foobar'}}
        producer = producer_pool['foobar'].acquire().__enter__()
        exchange = realtime.get_exchange()

        publisher = realtime.Publisher(pyramid_request)
        publisher.publish_annotation(payload)

        expected_headers = matchers.MappingContaining('timestamp')
        producer.publish.assert_called_once_with(payload,
                                                 exchange=exchange,
                                                 declare=[exchange],
                                                 routing_key='annotation',
                                                 headers=expected_headers)

    def test_publish_user(self, matchers, producer_pool, pyramid_request):
        payload = {'action': 'create', 'user': {'id': 'foobar'}}
        producer = producer_pool['foobar'].acquire().__enter__()
        exchange = realtime.get_exchange()

        publisher = realtime.Publisher(pyramid_request)
        publisher.publish_user(payload)

        expected_headers = matchers.MappingContaining('timestamp')
        producer.publish.assert_called_once_with(payload,
                                                 exchange=exchange,
                                                 declare=[exchange],
                                                 routing_key='user',
                                                 headers=expected_headers)

    @pytest.fixture
    def producer_pool(self, patch):
        return patch('h.realtime.producer_pool')


class TestGetExchange(object):
    def test_returns_the_exchange(self):
        import kombu
        exchange = realtime.get_exchange()
        assert isinstance(exchange, kombu.Exchange)

    def test_type(self):
        exchange = realtime.get_exchange()
        assert exchange.type == 'direct'

    def test_durable(self):
        exchange = realtime.get_exchange()
        assert exchange.durable is False

    def test_delivery_mode(self):
        """Test that delivery mode is 1 (transient)"""
        exchange = realtime.get_exchange()
        assert exchange.delivery_mode == 1


class TestGetConnection(object):
    def test_defaults(self, Connection):
        realtime.get_connection({})
        Connection.assert_called_once_with('amqp://guest:guest@localhost:5672//')

    def test_returns_the_connection(self, Connection):
        connection = realtime.get_connection({})
        assert connection == Connection.return_value

    def test_allows_to_overwrite_broker_url(self, Connection):
        broker_url = 'amqp://alice:bob@rabbitmq.int:5673/prj'
        realtime.get_connection({'broker_url': broker_url})
        Connection.assert_called_once_with(broker_url)

    @pytest.fixture
    def Connection(self, patch):
        return patch('h.realtime.kombu.Connection')


class TestDummyPublisher(object):

    def test_publish_annotation_does_nothing(self, pyramid_request):
        publisher = realtime.DummyPublisher(pyramid_request)
        publisher.publish_annotation({})

    def test_publish_user_does_nothing(self, pyramid_request):
        publisher = realtime.DummyPublisher(pyramid_request)
        publisher.publish_user({})


class TestConfiguration(object):

    def test_it_uses_dummy_publisher_when_using_sqs(self, pyramid_config):
        pyramid_config.add_request_method = mock.Mock(spec=pyramid_config.add_request_method)
        pyramid_config.registry = {'broker_url': 'sqs://'}

        realtime.includeme(pyramid_config)

        pyramid_config.add_request_method.assert_called_with(
            realtime.DummyPublisher,
            name='realtime',
            reify=True,
        )

    def test_it_uses_real_publisher_when_using_amqp(self, pyramid_config):
        pyramid_config.add_request_method = mock.Mock(spec=pyramid_config.add_request_method)
        pyramid_config.registry = {'broker_url': 'amqp://guest:guest@localhost:5672//'}

        realtime.includeme(pyramid_config)

        pyramid_config.add_request_method.assert_called_with(
            realtime.Publisher,
            name='realtime',
            reify=True,
        )
