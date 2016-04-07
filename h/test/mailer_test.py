# -*- coding: utf-8 -*-

import mock

from h import mailer


@mock.patch('h.mailer.celery', autospec=True)
@mock.patch('h.mailer.pyramid_mailer', autospec=True)
def test_send_creates_email_message(pyramid_mailer, celery):
    celery.request = mock.sentinel.request

    mailer.send(recipients=['foo@example.com'],
                subject='My email subject',
                body='Some text body')

    pyramid_mailer.message.Message.assert_called_once_with(
        subject='My email subject',
        recipients=['foo@example.com'],
        body='Some text body',
        html=None)


@mock.patch('h.mailer.celery', autospec=True)
@mock.patch('h.mailer.pyramid_mailer', autospec=True)
def test_send_creates_email_message_with_html_body(pyramid_mailer, celery):
    celery.request = mock.sentinel.request

    mailer.send(recipients=['foo@example.com'],
                subject='My email subject',
                body='Some text body',
                html='<p>An HTML body</p>')

    pyramid_mailer.message.Message.assert_called_once_with(
        subject='My email subject',
        recipients=['foo@example.com'],
        body='Some text body',
        html='<p>An HTML body</p>')


@mock.patch('h.mailer.celery', autospec=True)
@mock.patch('h.mailer.pyramid_mailer', autospec=True)
def test_send_dispatches_email_using_request_mailer(pyramid_mailer, celery):
    celery.request = mock.sentinel.request
    request_mailer = pyramid_mailer.get_mailer.return_value
    message = pyramid_mailer.message.Message.return_value

    mailer.send(recipients=['foo@example.com'],
                subject='My email subject',
                body='Some text body')

    pyramid_mailer.get_mailer.assert_called_once_with(mock.sentinel.request)
    request_mailer.send_immediately.assert_called_once_with(message)
