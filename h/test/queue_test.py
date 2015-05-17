from pyramid import testing
from mock import patch

from h import queue


@patch('nsq.reader.Reader')
def test_get_reader_default(fake_reader):
    req = testing.DummyRequest()
    queue.get_reader(req, 'ethics-in-games-journalism', 'channel4')
    fake_reader.assert_called_with('ethics-in-games-journalism',
                                   'channel4',
                                   nsqd_tcp_addresses=['localhost:4150'])


@patch('nsq.reader.Reader')
def test_get_reader(fake_reader):
    req = testing.DummyRequest()
    req.registry.settings.update({
        'nsq.reader.addresses': "foo:1234\nbar:4567"
    })
    queue.get_reader(req, 'ethics-in-games-journalism', 'channel4')
    fake_reader.assert_called_with('ethics-in-games-journalism',
                                   'channel4',
                                   nsqd_tcp_addresses=['foo:1234',
                                                       'bar:4567'])


@patch('nsq.reader.Reader')
def test_get_reader_namespace(fake_reader):
    """
    When the ``nsq.namespace`` setting is provided, `get_reader` should return
    a reader that automatically prefixes the namespace onto the name of the
    topic being read.
    """
    req = testing.DummyRequest()
    req.registry.settings.update({
        'nsq.namespace': "abc123"
    })
    queue.get_reader(req, 'safari', 'elephants')
    fake_reader.assert_called_with('abc123-safari',
                                   'elephants',
                                   nsqd_tcp_addresses=['localhost:4150'])


@patch('nsq.client.Client')
def test_get_writer_default(fake_writer):
    req = testing.DummyRequest()
    queue.get_writer(req)
    fake_writer.assert_called_with(nsqd_tcp_addresses=['localhost:4150'])


@patch('nsq.client.Client')
def test_get_writer(fake_writer):
    req = testing.DummyRequest()
    req.registry.settings.update({
        'nsq.writer.address': 'philae:2014'})
    queue.get_writer(req)
    fake_writer.assert_called_with(nsqd_tcp_addresses=['philae:2014'])


@patch('nsq.client.Client')
def test_get_writer_namespace(fake_writer):
    """
    When the ``nsq.namespace`` setting is provided, `get_writer` should return
    a writer that automatically prefixes the namespace onto the topic names.
    """
    req = testing.DummyRequest()
    req.registry.settings.update({
        'nsq.namespace': "abc123"
    })

    writer = queue.get_writer(req)
    fake_writer.assert_called_with(nsqd_tcp_addresses=['localhost:4150'])

    writer.pub('sometopic', 'somedata')
    fake_writer.pub.assert_called_with(writer, 'abc123-sometopic', 'somedata')

    writer.mpub('sometopic', 'somedata')
    fake_writer.mpub.assert_called_with(writer, 'abc123-sometopic', 'somedata')
