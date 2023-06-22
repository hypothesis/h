from unittest import mock

import pytest

from h import eventqueue


class DummyEvent:
    def __init__(self, request):
        # EventQueue currently assumes that events have a `request` attribute.
        self.request = request


@pytest.mark.usefixtures("pyramid_config")
class TestEventQueue:
    def test_init_adds_response_callback(self):
        request = mock.Mock()
        queue = eventqueue.EventQueue(request)

        request.add_response_callback.assert_called_once_with(queue.response_callback)

    def test_call_appends_event_to_queue(self):
        queue = eventqueue.EventQueue(mock.Mock())

        assert not queue.queue
        event = mock.Mock()
        queue(event)
        assert list(queue.queue) == [event]

    def test_publish_all_notifies_events_in_fifo_order(
        self, pyramid_request, subscriber
    ):
        queue = eventqueue.EventQueue(pyramid_request)
        firstevent = DummyEvent(pyramid_request)
        queue(firstevent)
        secondevent = DummyEvent(pyramid_request)
        queue(secondevent)

        queue.publish_all()

        assert subscriber.call_args_list == [
            mock.call(firstevent),
            mock.call(secondevent),
        ]

    def test_publish_all_sandboxes_each_subscriber(
        self, pyramid_request, pyramid_config
    ):
        queue = eventqueue.EventQueue(pyramid_request)

        first_subscriber = mock.Mock()
        second_subscriber = mock.Mock()
        second_subscriber.side_effect = ValueError
        third_subscriber = mock.Mock()

        subscribers = [first_subscriber, second_subscriber, third_subscriber]
        for sub in subscribers:
            pyramid_config.add_subscriber(sub, DummyEvent)

        event = DummyEvent(pyramid_request)

        queue(event)
        queue.publish_all()

        # If one subscriber raises an exception, that shouldn't prevent others
        # from running.
        for sub in subscribers:
            sub.assert_called_once_with(event)

    def test_publish_all_reraises_in_debug_mode(self, subscriber, pyramid_request):
        queue = eventqueue.EventQueue(pyramid_request)
        pyramid_request.debug = True
        subscriber.side_effect = ValueError("boom!")

        with pytest.raises(ValueError) as excinfo:
            queue(DummyEvent(pyramid_request))
            queue.publish_all()
        assert str(excinfo.value) == "boom!"

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
    def publish_all(self, patch):
        return patch("h.eventqueue.EventQueue.publish_all")

    @pytest.fixture
    def subscriber(self):
        return mock.Mock()

    @pytest.fixture
    def pyramid_config(self, pyramid_config, subscriber):
        pyramid_config.add_subscriber(subscriber, DummyEvent)
        return pyramid_config

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.debug = False
        pyramid_request.exception = None
        return pyramid_request
