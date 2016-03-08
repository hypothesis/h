# -*- coding: utf-8 -*-
import pytest
from pyramid import testing
from pyramid.testing import DummyRequest as _DummyRequest
from mock import patch

from h import queue


class DummySentry:
    def extra_context(self, context):
        pass


class DummyRegistry:
    pass


class DummyRequest(_DummyRequest):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('sentry', DummySentry())
        kwargs.setdefault('registry', DummyRegistry())
        super(DummyRequest, self).__init__(*args, **kwargs)


@patch('gnsq.Reader')
def test_get_reader_default(fake_reader):
    settings = {}
    queue.get_reader(settings, 'ethics-in-games-journalism', 'channel4')
    fake_reader.assert_called_with('ethics-in-games-journalism',
                                   'channel4',
                                   nsqd_tcp_addresses=['localhost:4150'])


@patch('gnsq.Reader')
def test_get_reader(fake_reader):
    settings = {'nsq.reader.addresses': "foo:1234\nbar:4567"}
    queue.get_reader(settings, 'ethics-in-games-journalism', 'channel4')
    fake_reader.assert_called_with('ethics-in-games-journalism',
                                   'channel4',
                                   nsqd_tcp_addresses=['foo:1234',
                                                       'bar:4567'])


@patch('gnsq.Reader')
def test_get_reader_namespace(fake_reader):
    """
    When the ``nsq.namespace`` setting is provided, `get_reader` should return
    a reader that automatically prefixes the namespace onto the name of the
    topic being read.
    """
    settings = {'nsq.namespace': "abc123"}
    queue.get_reader(settings, 'safari', 'elephants')
    fake_reader.assert_called_with('abc123-safari',
                                   'elephants',
                                   nsqd_tcp_addresses=['localhost:4150'])


@patch('raven.Client')
def test_get_reader_sentry_on_exception_hook(fake_client):
    settings = {}
    sentry = fake_client()
    reader = queue.get_reader(settings, 'safari', 'elephants',
                              sentry_client=sentry)
    reader.on_exception.send(error='An error happened')

    sentry.captureException.assert_called_with(exc_info=True,
                                               extra={'topic': 'safari'})


@patch('raven.Client')
def test_get_reader_sentry_on_error_hook(fake_client):
    settings = {}
    sentry = fake_client()
    reader = queue.get_reader(settings, 'safari', 'elephants',
                              sentry_client=sentry)
    reader.on_error.send()

    sentry.captureException.assert_called_with(
        exc_info=(type(None), None, None),
        extra={'topic': 'safari'})


@patch('raven.Client')
def test_get_reader_sentry_on_giving_up_hook(fake_client):
    settings = {}
    sentry = fake_client()
    reader = queue.get_reader(settings, 'safari', 'elephants',
                              sentry_client=sentry)
    reader.on_giving_up.send()

    sentry.captureMessage.assert_called_with(extra={'topic': 'safari'})


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
