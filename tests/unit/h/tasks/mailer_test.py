from unittest import mock

import pytest

from h.services.email import EmailData, EmailTag, LogData
from h.tasks import mailer


def test_send_without_log_data(email_service):
    email_data = {
        "recipients": ["foo@example.com"],
        "subject": "My email subject",
        "body": "Some text body",
        "tag": EmailTag.TEST,
    }
    mailer.send(email_data)

    email_service.send.assert_called_once_with(EmailData(**email_data), None)


def test_send_with_log_data(email_service):
    email_data = {
        "recipients": ["foo@example.com"],
        "subject": "My email subject",
        "body": "Some text body",
        "tag": EmailTag.TEST,
    }
    log_data = {
        "sender_id": 123,
        "recipient_ids": [456],
        "tag": EmailTag.TEST,
        "extra": {"annotation_id": "annotation_id"},
    }
    mailer.send(email_data, log_data)

    email_service.send.assert_called_once_with(
        EmailData(**email_data), LogData(**log_data)
    )


def test_send_retries_if_mailing_fails(email_service):
    email_service.send.side_effect = Exception()
    mailer.send.retry = mock.Mock(wraps=mailer.send.retry)

    email_data = {
        "recipients": ["foo@example.com"],
        "subject": "My email subject",
        "body": "Some text body",
        "tag": EmailTag.TEST,
    }
    with pytest.raises(Exception):  # noqa: B017, PT011
        mailer.send(email_data)

    assert mailer.send.retry.called


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.debug = False
    return pyramid_request


@pytest.fixture(autouse=True)
def celery(patch, pyramid_request):
    celery = patch("h.tasks.mailer.celery")
    celery.request = pyramid_request
    return celery
