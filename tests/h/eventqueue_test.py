# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import mock
import pytest

from h import eventqueue


class DummyEvent(object):
    def __init__(self, request):
        # EventQueue currently assumes that events have a `request` attribute.
        self.request = request


class TestEventQueue(object):
    def test_init_adds_response_callback(self, queue, pyramid_request):
        pyramid_request.add_response_callback = mock.Mock(autospec=pyramid_request.add_response_callback)
        queue = eventqueue.EventQueue(pyramid_request)
        pyramid_request.add_response_callback.assert_called_once_with(queue.response_callback)

    def test_call_appends_event_to_queue(self, queue, event):
        assert len(queue.queue) == 0

        queue(event)
        assert list(queue.queue) == [event]

    def test_publish_all_notifies_events_in_fifo_order(self, queue, subscriber, event_factory, pyramid_config):
        pyramid_config.add_subscriber(subscriber, DummyEvent)
        firstevent = event_factory.get()
        secondevent = event_factory.get()

        queue(firstevent)
        queue(secondevent)

        queue.publish_all()

        subscriber.assert_has_calls([mock.call(firstevent), mock.call(secondevent)])

    def test_publish_all_sandboxes_each_subscriber(self, event, subscriber_factory, failing_subscriber, pyramid_config, queue):
        subscribers = [
            subscriber_factory.get(),
            failing_subscriber,
            subscriber_factory.get()]

        for sub in subscribers:
            pyramid_config.add_subscriber(sub, DummyEvent)

        queue(event)
        queue.publish_all()

        # If one subscriber raises an exception, that shouldn't prevent others
        # from running.
        for sub in subscribers:
            sub.assert_called_once_with(event)

    def test_publish_all_reraises_in_debug_mode(self, failing_subscriber, event, queue, pyramid_request, pyramid_config):
        pyramid_config.add_subscriber(failing_subscriber, DummyEvent)
        pyramid_request.debug = True

        with pytest.raises(Exception) as excinfo:
            queue(event)
            queue.publish_all()
        assert str(excinfo.value) == 'boom!'

    def test_publish_all_sends_exception_to_sentry(self, failing_subscriber, event, queue, pyramid_request, pyramid_config):
        pyramid_config.add_subscriber(failing_subscriber, DummyEvent)
        pyramid_request.sentry = mock.Mock(spec_set=['captureException'])
        queue(event)

        queue.publish_all()

        assert pyramid_request.sentry.captureException.called

    def test_publish_all_logs_exception_when_sentry_is_not_available(self, log, failing_subscriber, event, queue, pyramid_config):
        pyramid_config.add_subscriber(failing_subscriber, DummyEvent)
        queue(event)

        queue.publish_all()

        assert log.exception.called

    def test_response_callback_skips_publishing_events_on_exception(self, publish_all, queue, pyramid_request):
        pyramid_request.exception = ValueError('exploded!')
        queue.response_callback(pyramid_request, None)
        assert not publish_all.called

    def test_response_callback_publishes_events(self, publish_all, event, queue, pyramid_request):
        queue(event)
        queue.response_callback(pyramid_request, None)
        assert publish_all.called

    @pytest.fixture
    def log(self, patch):
        return patch('h.eventqueue.log', autospec=True)

    @pytest.fixture
    def publish_all(self, patch):
        return patch('h.eventqueue.EventQueue.publish_all', autospec=True)

    @pytest.fixture
    def event(self, event_factory):
        return event_factory.get()

    @pytest.fixture
    def event_factory(self, pyramid_request):

        class EventFactory():
            def get(self):
                return DummyEvent(pyramid_request)

        return EventFactory()

    @pytest.fixture
    def subscriber(self, subscriber_factory):
        return subscriber_factory.get()

    @pytest.fixture
    def failing_subscriber(self, subscriber_factory):
        sub = subscriber_factory.get()
        sub.side_effect = Exception("boom!")
        return sub

    @pytest.fixture
    def subscriber_factory(self):
        class SubscriberFactory():
            def get(self):
                return mock.Mock()
        return SubscriberFactory()

    @pytest.fixture
    def queue(self, pyramid_request):
        return eventqueue.EventQueue(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.debug = False
        pyramid_request.exception = None
        return pyramid_request
