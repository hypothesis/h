# -*- coding: utf-8 -*-

from collections import namedtuple

import pytest
from mock import Mock
from mock import patch

import blinker

from h import queue


FakeMessage = namedtuple('FakeMessage', ['body'])


class FakeReader(object):
    """
    A fake `gnsq.Reader` class.

    This is swapped out automatically for every test in this module by the
    `fake_reader` fixture.
    """
    on_exception = blinker.Signal()
    on_error = blinker.Signal()
    on_giving_up = blinker.Signal()

    def __init__(self, topic, channel, **kwargs):
        self.topic = topic
        self.channel = channel
        self.kwargs = kwargs

    def simulate_exception(self, message=None, error=None):
        if message is None:
            message = FakeMessage(body="a message")
        if error is None:
            error = RuntimeError("explosion!")
        self.on_exception.send(self, message=message, error=error)

    def simulate_error(self, error=None):
        if error is None:
            error = RuntimeError("explosion!")
        self.on_error.send(self, error=error)

    def simulate_giving_up(self, message=None):
        if message is None:
            message = FakeMessage(body="a message")
        self.on_giving_up.send(self, message=message)


class FakeClient(object):
    """A fake `raven.Client` class."""

    captureException = Mock(spec=[])
    captureMessage = Mock(spec=[])


def test_get_reader_default():
    settings = {}

    reader = queue.get_reader(settings,
                              'ethics-in-games-journalism',
                              'channel4')

    assert reader.topic == 'ethics-in-games-journalism'
    assert reader.channel == 'channel4'
    assert reader.kwargs['nsqd_tcp_addresses'] == ['localhost:4150']


def test_get_reader_respects_address_settings():
    settings = {'nsq.reader.addresses': "foo:1234\nbar:4567"}

    reader = queue.get_reader(settings,
                              'ethics-in-games-journalism',
                              'channel4')

    assert reader.kwargs['nsqd_tcp_addresses'] == ['foo:1234', 'bar:4567']


def test_get_reader_uses_namespace():
    """
    When the ``nsq.namespace`` setting is provided, `get_reader` should return
    a reader that automatically prefixes the namespace onto the name of the
    topic being read.
    """
    settings = {'nsq.namespace': "abc123"}

    reader = queue.get_reader(settings, 'safari', 'elephants')

    assert reader.topic == 'abc123-safari'


def test_get_reader_connects_on_exception_hook_to_sentry_client():
    settings = {}
    client = FakeClient()
    reader = queue.get_reader(settings,
                              'safari',
                              'elephants',
                              sentry_client=client)

    reader.simulate_exception(message=FakeMessage("foobar"))

    client.captureException.assert_called_with(exc_info=True,
                                               extra={'topic': 'safari',
                                                      'channel': 'elephants',
                                                      'message': 'foobar'})


def test_get_reader_connects_on_error_hook_to_sentry_client():
    settings = {}
    client = FakeClient()
    reader = queue.get_reader(settings,
                              'safari',
                              'elephants',
                              sentry_client=client)

    error = RuntimeError("asplode!")
    reader.simulate_error(error=error)

    client.captureException.assert_called_with(
        exc_info=(RuntimeError, error, None),
        extra={'topic': 'safari', 'channel': 'elephants'})


def test_get_reader_connects_on_giving_up_hook_to_sentry_client():
    settings = {}
    client = FakeClient()
    reader = queue.get_reader(settings,
                              'safari',
                              'elephants',
                              sentry_client=client)

    reader.simulate_giving_up(message=FakeMessage("nopeski"))

    client.captureMessage.assert_called_with("Giving up on message",
                                             extra={'topic': 'safari',
                                                    'channel': 'elephants',
                                                    'message': 'nopeski'})


@patch('gnsq.Nsqd')
def test_get_writer_default(fake_nsqd):
    settings = {}
    queue.get_writer(settings)
    fake_nsqd.assert_called_with('localhost', http_port='4151')


@patch('gnsq.Nsqd')
def test_get_writer(fake_nsqd):
    settings = {'nsq.writer.address': 'philae:2014'}
    queue.get_writer(settings)
    fake_nsqd.assert_called_with('philae', http_port='2014')


@patch('gnsq.Nsqd')
def test_get_writer_namespace(fake_nsqd):
    """
    When the ``nsq.namespace`` setting is provided, `get_writer` should return
    a writer that automatically prefixes the namespace onto the topic names
    given to :method:`gnsq.Nsqd.publish` or :method:`gnsq.Nsqd.mpublish`.
    """
    settings = {'nsq.namespace': "abc123"}
    fake_client = fake_nsqd.return_value

    writer = queue.get_writer(settings)

    writer.publish('sometopic', 'somedata')
    fake_client.publish.assert_called_with('abc123-sometopic', 'somedata')


@patch('gnsq.Nsqd')
def test_writer_serializes_dict(fake_nsqd):
    settings = {'nsq.namespace': 'abc'}
    fake_client = fake_nsqd.return_value
    writer = queue.get_writer(settings)
    writer.publish('sometopic', {
        'key': 'value',
    })
    fake_client.publish.assert_called_with('abc-sometopic', '{"key": "value"}')


@pytest.mark.parametrize('topic,namespace,settings_obj,expected', [
    # No namespace
    ('foo', None, None, 'foo'),
    ('foo', None, {}, 'foo'),
    ('foo', None, {'nsq.namespace': None}, 'foo'),
    # Namespace provided
    ('foo', 'myns', None, 'myns-foo'),
    ('foo', None, {'nsq.namespace': 'myns'}, 'myns-foo'),
])
def test_resolve_topic(topic, namespace, settings_obj, expected):
    result = queue.resolve_topic(topic,
                                 namespace=namespace,
                                 settings=settings_obj)

    assert result == expected


def test_resolve_topic_raises_if_namespace_and_topic_both_given():
    with pytest.raises(ValueError):
        queue.resolve_topic('foo',
                            namespace='prefix',
                            settings={'nsq.namespace': 'prefix'})


@pytest.fixture(autouse=True)
def fake_reader(patch):
    return patch('gnsq.Reader', autospec=None, new_callable=lambda: FakeReader)
