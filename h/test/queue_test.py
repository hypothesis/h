import pytest
from pyramid import testing
from mock import patch

from h import queue


@patch('gnsq.Reader')
def test_get_reader_default(fake_reader):
    req = testing.DummyRequest()
    queue.get_reader(req, 'ethics-in-games-journalism', 'channel4')
    fake_reader.assert_called_with('ethics-in-games-journalism',
                                   'channel4',
                                   nsqd_tcp_addresses=['localhost:4150'])


@patch('gnsq.Reader')
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

@patch('gnsq.Reader')
def test_get_reader_namespace(fake_reader):
    req = testing.DummyRequest()
    req.registry.settings.update({
        'nsq.namespace': "abc123"
    })
    queue.get_reader(req, 'safari', 'elephants')
    fake_reader.assert_called_with('abc123-safari',
                                   'elephants',
                                   nsqd_tcp_addresses=['localhost:4150'])


@patch('gnsq.Nsqd')
def test_get_writer_default(fake_nsqd):
    req = testing.DummyRequest()
    queue.get_writer(req)
    fake_nsqd.assert_called_with('localhost', http_port='4151')


@patch('gnsq.Nsqd')
def test_get_writer(fake_nsqd):
    req = testing.DummyRequest()
    req.registry.settings.update({'nsq.writer.address': 'philae:2014'})
    queue.get_writer(req)
    fake_nsqd.assert_called_with('philae', http_port='2014')
