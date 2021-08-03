from smtplib import SMTPServerDisconnected
from unittest import mock

import pytest

from h.tasks import mailer


@mock.patch("h.tasks.mailer.celery", autospec=True)
@mock.patch("h.tasks.mailer.pyramid_mailer", autospec=True)
def test_send_creates_email_message(pyramid_mailer, celery, pyramid_request):
    celery.request = pyramid_request

    mailer.send(  # pylint:disable=no-value-for-parameter #: (bound celery task)
        recipients=["foo@example.com"],
        subject="My email subject",
        body="Some text body",
    )

    pyramid_mailer.message.Message.assert_called_once_with(
        subject="My email subject",
        recipients=["foo@example.com"],
        body="Some text body",
        html=None,
    )


@mock.patch("h.tasks.mailer.celery", autospec=True)
@mock.patch("h.tasks.mailer.pyramid_mailer", autospec=True)
def test_send_creates_email_message_with_html_body(
    pyramid_mailer, celery, pyramid_request
):
    celery.request = pyramid_request

    mailer.send(  # pylint:disable=no-value-for-parameter #: (bound celery task)
        recipients=["foo@example.com"],
        subject="My email subject",
        body="Some text body",
        html="<p>An HTML body</p>",
    )

    pyramid_mailer.message.Message.assert_called_once_with(
        subject="My email subject",
        recipients=["foo@example.com"],
        body="Some text body",
        html="<p>An HTML body</p>",
    )


@mock.patch("h.tasks.mailer.celery", autospec=True)
@mock.patch("h.tasks.mailer.pyramid_mailer", autospec=True)
def test_send_dispatches_email_using_request_mailer(
    pyramid_mailer, celery, pyramid_request
):
    celery.request = pyramid_request
    request_mailer = pyramid_mailer.get_mailer.return_value
    message = pyramid_mailer.message.Message.return_value

    mailer.send(  # pylint:disable=no-value-for-parameter #: (bound celery task)
        recipients=["foo@example.com"],
        subject="My email subject",
        body="Some text body",
    )

    pyramid_mailer.get_mailer.assert_called_once_with(pyramid_request)
    request_mailer.send_immediately.assert_called_once_with(message)


@mock.patch("h.tasks.mailer.celery", autospec=True)
@mock.patch("h.tasks.mailer.pyramid_mailer", autospec=True)
def test_send_retries_if_mailing_fails(pyramid_mailer, celery, pyramid_request):
    celery.request = pyramid_request
    request_mailer = pyramid_mailer.get_mailer.return_value
    request_mailer.send_immediately.side_effect = SMTPServerDisconnected()

    mailer.send.retry = mock.Mock(spec_set=[])
    mailer.send(  # pylint:disable=no-value-for-parameter #: bound celery task
        recipients=["foo@example.com"],
        subject="My email subject",
        body="Some text body",
    )

    assert mailer.send.retry.called


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.debug = False
    return pyramid_request
