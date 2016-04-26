# -*- coding: utf-8 -*-

import mock
import pytest

from pyramid.testing import DummyRequest

from h import app


class TestEventQueue(object):
    def test_init_adds_response_callback(self):
        request = mock.Mock()
        queue = app.EventQueue(request)

        request.add_response_callback.assert_called_once_with(queue.response_callback)

    def test_call_appends_event_to_queue(self):
        queue = app.EventQueue(mock.Mock())

        assert len(queue.queue) == 0
        event = mock.Mock()
        queue(event)
        assert list(queue.queue) == [event]

    def test_publish_all_notifies_events_in_fifo_order(self):
        request = DummyRequest()
        request.registry.notify = mock.Mock(spec=lambda event: None)
        queue = app.EventQueue(request)
        firstevent = mock.Mock()
        queue(firstevent)
        secondevent = mock.Mock()
        queue(secondevent)

        queue.publish_all()

        assert request.registry.notify.call_args_list == [
            mock.call(firstevent),
            mock.call(secondevent)
        ]

    def test_response_callback_skips_publishing_events_on_exception(self, publish_all):
        request = DummyRequest(exception=ValueError('exploded!'))
        queue = app.EventQueue(request)
        queue.response_callback(request, None)
        assert not publish_all.called

    def test_response_callback_publishes_events(self, publish_all):
        request = DummyRequest(exception=None, tm=mock.MagicMock())
        queue = app.EventQueue(request)
        queue(mock.Mock())
        queue.response_callback(request, None)
        assert publish_all.called

    @pytest.fixture
    def publish_all(self, patch):
        return patch('h.app.EventQueue.publish_all')
