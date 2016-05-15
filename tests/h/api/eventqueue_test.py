# -*- coding: utf-8 -*-

import mock
import pytest

from pyramid.testing import DummyRequest

from h.api import eventqueue


class TestEventQueue(object):
    def test_init_adds_response_callback(self, mock_request):
        request = mock.Mock()
        queue = eventqueue.EventQueue(request)

        request.add_response_callback.assert_called_once_with(queue.response_callback)

    def test_call_appends_event_to_queue(self):
        queue = eventqueue.EventQueue(mock.Mock())

        assert len(queue.queue) == 0
        event = mock.Mock()
        queue(event)
        assert list(queue.queue) == [event]

    def test_publish_all_notifies_events_in_fifo_order(self, mock_request):
        queue = eventqueue.EventQueue(mock_request)
        firstevent = mock.Mock(request=mock_request)
        queue(firstevent)
        secondevent = mock.Mock(request=mock_request)
        queue(secondevent)

        queue.publish_all()

        assert mock_request.registry.notify.call_args_list == [
            mock.call(firstevent),
            mock.call(secondevent)
        ]

    def test_publish_all_sanboxes_each_event(self, mock_request):
        queue = eventqueue.EventQueue(mock_request)
        firstevent = mock.Mock(request=mock_request)
        queue(firstevent)
        secondevent = mock.Mock(request=mock_request)
        queue(secondevent)

        queue.publish_all()

        assert mock_request.registry.notify.call_args_list == [
            mock.call(firstevent),
            mock.call(secondevent)
        ]

    def test_publish_all_sends_exception_to_sentry(self, mock_request):
        mock_request.sentry = mock.Mock()
        mock_request.registry.notify.side_effect = ValueError('exploded!')
        queue = eventqueue.EventQueue(mock_request)
        event = mock.Mock(request=mock_request)
        queue(event)

        queue.publish_all()
        assert mock_request.sentry.captureException.called

    def test_publish_all_logs_exception_when_sentry_is_not_available(self, mock_request, log):
        mock_request.registry.notify.side_effect = ValueError('exploded!')
        queue = eventqueue.EventQueue(mock_request)
        event = mock.Mock(request=mock_request)
        queue(event)

        queue.publish_all()

        assert log.exception.called

    def test_response_callback_skips_publishing_events_on_exception(self, publish_all):
        request = DummyRequest(exception=ValueError('exploded!'))
        queue = eventqueue.EventQueue(request)
        queue.response_callback(request, None)
        assert not publish_all.called

    def test_response_callback_publishes_events(self, publish_all):
        request = DummyRequest(exception=None, tm=mock.MagicMock())
        queue = eventqueue.EventQueue(request)
        queue(mock.Mock())
        queue.response_callback(request, None)
        assert publish_all.called

    @pytest.fixture
    def mock_request(self):
        request = DummyRequest(debug=False)
        request.registry.notify = mock.Mock()
        return request

    @pytest.fixture
    def log(self, patch):
        return patch('h.api.eventqueue.log')

    @pytest.fixture
    def publish_all(self, patch):
        return patch('h.api.eventqueue.EventQueue.publish_all')
