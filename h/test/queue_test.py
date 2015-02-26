from pyramid import testing
from mock import patch

from ..queue import get_reader
from ..queue import get_writer


@patch('gnsq.Reader')
def test_get_reader_default(fake_reader):
    req = testing.DummyRequest()
    get_reader(req, 'ethics-in-games-journalism', 'channel4')
    fake_reader.assert_called_with('ethics-in-games-journalism',
                                   'channel4',
                                   nsqd_tcp_addresses=['localhost:4150'])


@patch('gnsq.Reader')
def test_get_reader(fake_reader):
    req = testing.DummyRequest()
    req.registry.settings.update({
        'nsq.reader.addresses': "foo:1234\nbar:4567"
    })
    get_reader(req, 'ethics-in-games-journalism', 'channel4')
    fake_reader.assert_called_with('ethics-in-games-journalism',
                                   'channel4',
                                   nsqd_tcp_addresses=['foo:1234',
                                                       'bar:4567'])


@patch('gnsq.Nsqd')
def test_get_writer_default(fake_nsqd):
    req = testing.DummyRequest()
    get_writer(req)
    fake_nsqd.assert_called_with('localhost', http_port='4151')


@patch('gnsq.Nsqd')
def test_get_writer(fake_nsqd):
    req = testing.DummyRequest()
    req.registry.settings.update({'nsq.writer.address': 'philae:2014'})
    get_writer(req)
    fake_nsqd.assert_called_with('philae', http_port='2014')
