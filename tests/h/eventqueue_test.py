# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import mock
import pytest

from h import eventqueue


class TestEventQueue(object):
    def test_init_adds_response_callback(self, pyramid_request):
        request = mock.Mock()
        queue = eventqueue.EventQueue(request)

        request.add_response_callback.assert_called_once_with(queue.response_callback)

    def test_call_appends_event_to_queue(self):
        queue = eventqueue.EventQueue(mock.Mock())

        assert len(queue.queue) == 0
        event = mock.Mock()
        queue(event)
        assert list(queue.queue) == [event]

    def test_publish_all_notifies_events_in_fifo_order(self, notify, pyramid_request):
        queue = eventqueue.EventQueue(pyramid_request)
        firstevent = mock.Mock(request=pyramid_request)
        queue(firstevent)
        secondevent = mock.Mock(request=pyramid_request)
        queue(secondevent)

        queue.publish_all()

        assert notify.call_args_list == [mock.call(firstevent), mock.call(secondevent)]

    def test_publish_all_sandboxes_each_event(self, notify, pyramid_request):
        queue = eventqueue.EventQueue(pyramid_request)
        firstevent = mock.Mock(request=pyramid_request)
        queue(firstevent)
        secondevent = mock.Mock(request=pyramid_request)
        queue(secondevent)

        queue.publish_all()

        assert notify.call_args_list == [mock.call(firstevent), mock.call(secondevent)]

    def test_publish_all_sends_exception_to_sentry(self, notify, pyramid_request):
        pyramid_request.sentry = mock.Mock()
        notify.side_effect = ValueError("exploded!")
        queue = eventqueue.EventQueue(pyramid_request)
        event = mock.Mock(request=pyramid_request)
        queue(event)

        queue.publish_all()
        assert pyramid_request.sentry.captureException.called

    def test_publish_all_logs_exception_when_sentry_is_not_available(
        self, log, notify, pyramid_request
    ):
        notify.side_effect = ValueError("exploded!")
        queue = eventqueue.EventQueue(pyramid_request)
        event = mock.Mock(request=pyramid_request)
        queue(event)

        queue.publish_all()

        assert log.exception.called

    def test_response_callback_skips_publishing_events_on_exception(
        self, publish_all, pyramid_request
    ):
        pyramid_request.exception = ValueError("exploded!")
        queue = eventqueue.EventQueue(pyramid_request)
        queue.response_callback(pyramid_request, None)
        assert not publish_all.called

    def test_response_callback_publishes_events(self, publish_all, pyramid_request):
        queue = eventqueue.EventQueue(pyramid_request)
        queue(mock.Mock())
        queue.response_callback(pyramid_request, None)
        assert publish_all.called

    @pytest.fixture
    def log(self, patch):
        return patch("h.eventqueue.log")

    @pytest.fixture
    def publish_all(self, patch):
        return patch("h.eventqueue.EventQueue.publish_all")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.debug = False
        pyramid_request.exception = None
        return pyramid_request
