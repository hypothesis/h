from mock import patch

from h.queue import get_reader
from h.queue import get_writer


@patch('gnsq.Reader')
def test_get_reader_default(fake_reader):
    get_reader({}, 'ethics-in-games-journalism', 'channel4')
    fake_reader.assert_called_with('ethics-in-games-journalism',
                                   'channel4',
                                   nsqd_tcp_addresses=['localhost:4150'])


@patch('gnsq.Reader')
def test_get_reader(fake_reader):
    get_reader({'nsq.reader.addresses': "foo:1234\nbar:4567"},
               'ethics-in-games-journalism',
               'channel4')
    fake_reader.assert_called_with('ethics-in-games-journalism',
                                   'channel4',
                                   nsqd_tcp_addresses=['foo:1234',
                                                       'bar:4567'])


@patch('gnsq.Nsqd')
def test_get_writer_default(fake_nsqd):
    get_writer({})
    fake_nsqd.assert_called_with('localhost', http_port='4151')


@patch('gnsq.Nsqd')
def test_get_writer(fake_nsqd):
    get_writer({'nsq.writer.address': 'philae:2014'})
    fake_nsqd.assert_called_with('philae', http_port='2014')
