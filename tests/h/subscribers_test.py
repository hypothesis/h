# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest
from pyramid import testing

from h import subscribers
from h.api.events import AnnotationEvent


class FakeMailer(object):
    def __init__(self):
        self.lastcall = None

    def __call__(self, recipients, subject, body, html):
        self.lastcall = (recipients, subject, body, html)


class TestPublishAnnotationEvent:

    def test_it_publishes_the_realtime_event(self, event):
        event.request.headers = {'X-Client-Id': 'client_id'}

        subscribers.publish_annotation_event(event)

        event.request.realtime.publish_annotation.assert_called_once_with({
            'action': event.action,
            'annotation_id': event.annotation_id,
            'src_client_id': 'client_id'
        })

    @pytest.fixture
    def event(self):
        return mock.Mock(
            spec=AnnotationEvent(testing.DummyRequest(),
                                 'test_annotation_id',
                                 'create'),
        )


@pytest.mark.usefixtures('fetch_annotation')
class TestSendReplyNotifications(object):
    def test_calls_get_notification_with_request_annotation_and_action(self, fetch_annotation):
        send = FakeMailer()
        get_notification = mock.Mock(spec_set=[], return_value=None)
        generate_mail = mock.Mock(spec_set=[], return_value=[])
        event = AnnotationEvent(mock.sentinel.request,
                                mock.sentinel.annotation_id,
                                mock.sentinel.action)
        mock.sentinel.request.db = mock.Mock()

        subscribers.send_reply_notifications(event,
                                             get_notification=get_notification,
                                             generate_mail=generate_mail,
                                             send=send)

        fetch_annotation.assert_called_once_with(mock.sentinel.request.db,
                                                 mock.sentinel.annotation_id)

        get_notification.assert_called_once_with(mock.sentinel.request,
                                                 fetch_annotation.return_value,
                                                 mock.sentinel.action)

    def test_generates_and_sends_mail_for_any_notification(self):
        s = mock.sentinel
        send = FakeMailer()
        get_notification = mock.Mock(spec_set=[], return_value=s.notification)
        generate_mail = mock.Mock(spec_set=[])
        generate_mail.return_value = (['foo@example.com'], 'Your email', 'Text body', 'HTML body')
        event = AnnotationEvent(s.request, None, None)
        s.request.db = mock.Mock()

        subscribers.send_reply_notifications(event,
                                             get_notification=get_notification,
                                             generate_mail=generate_mail,
                                             send=send)

        generate_mail.assert_called_once_with(s.request, s.notification)
        assert send.lastcall == (['foo@example.com'], 'Your email', 'Text body', 'HTML body')

    def test_catches_exceptions_and_reports_to_sentry(self):
        send = FakeMailer()
        get_notification = mock.Mock(spec_set=[], side_effect=RuntimeError('asplode!'))
        generate_mail = mock.Mock(spec_set=[], return_value=[])
        request = testing.DummyRequest(sentry=mock.Mock(), db=mock.Mock(), debug=False)
        event = AnnotationEvent(request, None, None)

        subscribers.send_reply_notifications(event,
                                             get_notification=get_notification,
                                             generate_mail=generate_mail,
                                             send=send)

        event.request.sentry.captureException.assert_called_once_with()

    def test_reraises_exceptions_in_debug_mode(self):
        send = FakeMailer()
        get_notification = mock.Mock(spec_set=[], side_effect=RuntimeError('asplode!'))
        generate_mail = mock.Mock(spec_set=[], return_value=[])
        request = testing.DummyRequest(sentry=mock.Mock(), db=mock.Mock(), debug=True)
        event = AnnotationEvent(request, None, None)

        with pytest.raises(RuntimeError):
            subscribers.send_reply_notifications(event,
                                                 get_notification=get_notification,
                                                 generate_mail=generate_mail,
                                                 send=send)

    @pytest.fixture
    def fetch_annotation(self, patch):
        return patch('h.subscribers.storage.fetch_annotation')
