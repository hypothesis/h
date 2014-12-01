import gevent

from mock import ANY
from mock import patch
import unittest

import h.queue.local
from h.queue.local import LocalQueueHelper
from h.queue.local import Reader
from h.queue.local import Writer


class TestReader(unittest.TestCase):
    def setUp(self):
        self.queue_patcher = patch('gevent.queue.Queue')
        self.queue = self.queue_patcher.start()
        self.spawn_patcher = patch('gevent.spawn')
        self.spawn = self.spawn_patcher.start()

    def tearDown(self):
        self.queue_patcher.stop()
        self.spawn_patcher.stop()
        # Clear any thread-local state after each test
        h.queue.local.QUEUES.clear()

    def test_start_reads_queue(self):
        r = Reader('mytopic', 'mychannel')
        r.start(block=False)

        self.spawn.assert_called_with(ANY, self.queue.return_value)

    def test_start_blocking_joins_reader(self):
        r = Reader('mytopic', 'mychannel')
        r.start()

        self.spawn.return_value.join.assert_called_once()

    def test_start_is_idempotent(self):
        r = Reader('mytopic', 'mychannel')
        r.start(block=False)
        r.start(block=False)

        self.queue.assert_called_once()

    def test_join(self):
        r = Reader('mytopic', 'mychannel')
        r.start(block=False)
        r.join()

        self.spawn.return_value.join.assert_called_once()

    def test_close(self):
        r = Reader('mytopic', 'mychannel')
        r.start(block=False)
        r.close()

        self.spawn.return_value.kill.assert_called_once()


class TestWriter(unittest.TestCase):
    def tearDown(self):
        # Clear any thread-local state after each test
        h.queue.local.QUEUES.clear()

    @patch('gevent.queue.Queue')
    def test_publish_queues_message(self, fake_queue):
        w = Writer()
        w.publish('giraffes', {'neck': 'long'})

        fake_queue.return_value.put.assert_called_once()

    @patch('gevent.queue.Queue')
    def test_publish_wraps_message_object(self, fake_queue):
        w = Writer()
        w.publish('giraffes', {'neck': 'long'})

        msg = fake_queue.return_value.put.call_args[0][0]
        assert msg.body == {'neck': 'long'}


def test_queue_integration():
    messages = []

    helper = LocalQueueHelper({})

    reader = helper.get_reader('foo', 'bar')
    writer = helper.get_writer()

    reader.on_message.connect(lambda r, message: messages.append(message),
                              weak=False)
    reader.start(block=False)

    writer.publish('foo', {"just": "some data"})
    writer.publish('bar', {"other": "things"})

    gevent.sleep()
    reader.close()

    assert len(messages) == 1
    assert messages[0].body == {"just": "some data"}
