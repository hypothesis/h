# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest
from pyramid import testing

from h import subscribers
from h.api import models
from h.api.events import AnnotationEvent


class FakeMailer(object):
    def __init__(self):
        self.calls = []

    def __call__(self, recipients, subject, body, html):
        self.calls.append((recipients, subject, body, html))


def fake_generate(data=None):
    def generate(*args):
        if data:
            for item in data:
                yield item
    return generate


@pytest.mark.usefixtures('json', 'presenters')
class TestPublishAnnotationEvent:

    def test_it_gets_the_queue_writer(self, event):
        subscribers.publish_annotation_event(event)

        event.request.get_queue_writer.assert_called_once_with()

    def test_it_presents_the_annotation(self, event, presenters):
        subscribers.publish_annotation_event(event)

        presenters.AnnotationJSONPresenter.assert_called_once_with(
            event.request,
            event.annotation,
        )
        presenters.AnnotationJSONPresenter.return_value.asdict\
            .assert_called_once_with()

    def test_it_serializes_the_data(self, event, json, presenters):
        event.request.headers = {'X-Client-Id': 'client_id'}

        subscribers.publish_annotation_event(event)

        json.dumps.assert_called_once_with({
            'action': event.action,
            'annotation': presenters.AnnotationJSONPresenter
                .return_value.asdict.return_value,
            'src_client_id': 'client_id',
        })

    def test_it_publishes_the_serialized_data(self, event, json):
        subscribers.publish_annotation_event(event)

        event.request.get_queue_writer.return_value.publish\
            .assert_called_once_with(
                'annotations',
                json.dumps.return_value)

    @pytest.fixture
    def event(self):
        return mock.Mock(
            spec=AnnotationEvent(testing.DummyRequest(),
                                 mock.Mock(spec=models.Annotation()),
                                 'create'),
        )

    @pytest.fixture
    def json(self, patch):
        return patch('h.subscribers.json')

    @pytest.fixture
    def presenters(self, patch):
        return patch('h.subscribers.presenters')


class TestSendReplyNotifications(object):
    def test_calls_generate_with_request_annotation_and_action(self):
        send = FakeMailer()
        generate = mock.Mock(spec_set=[], return_value=[])
        event = AnnotationEvent(mock.sentinel.request,
                                mock.sentinel.annotation,
                                mock.sentinel.action)

        subscribers.send_reply_notifications(event,
                                             generate=generate,
                                             send=send)

        generate.assert_called_once_with(mock.sentinel.request,
                                         mock.sentinel.annotation,
                                         mock.sentinel.action)

    def test_sends_mail_generated_by_generate(self):
        send = FakeMailer()
        generate = fake_generate([
            ('Your email', 'Text body', 'HTML body', ['foo@example.com']),
            ('Safari', 'Giraffes', '<p>Elephants!</p>', ['bar@example.com']),
        ])
        event = AnnotationEvent(None, None, None)

        subscribers.send_reply_notifications(event,
                                             generate=generate,
                                             send=send)

        assert send.calls == [
            (['foo@example.com'], 'Your email', 'Text body', 'HTML body'),
            (['bar@example.com'], 'Safari', 'Giraffes', '<p>Elephants!</p>'),
        ]

    def test_catches_exceptions_and_reports_to_sentry(self):
        send = FakeMailer()
        generate = mock.Mock(spec_set=[], side_effect=RuntimeError('asplode!'))
        request = testing.DummyRequest(sentry=mock.Mock(), debug=False)
        event = AnnotationEvent(request, None, None)

        subscribers.send_reply_notifications(event,
                                             generate=generate,
                                             send=send)

        event.request.sentry.captureException.assert_called_once_with()

    def test_reraises_exceptions_in_debug_mode(self):
        send = FakeMailer()
        generate = mock.Mock(spec_set=[], side_effect=RuntimeError('asplode!'))
        request = testing.DummyRequest(sentry=mock.Mock(), debug=True)
        event = AnnotationEvent(request, None, None)

        with pytest.raises(RuntimeError):
            subscribers.send_reply_notifications(event,
                                                 generate=generate,
                                                 send=send)
