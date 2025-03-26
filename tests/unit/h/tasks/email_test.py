from unittest import mock

import pytest

from h.services.email import EmailData, EmailTag, LogData
from h.tasks import email


def test_send(email_data, log_data, email_service):
    email.send(email_data, log_data)

    email_service.send.assert_called_once_with(
        EmailData(**email_data), LogData(**log_data)
    )


def test_send_retries_if_mailing_fails(email_data, log_data, email_service):
    email_service.send.side_effect = Exception()
    email.send.retry = mock.Mock(wraps=email.send.retry)

    with pytest.raises(Exception) as exc_info:  # noqa: PT011
        email.send(email_data, log_data)
    assert exc_info.type is Exception

    assert email.send.retry.called


@pytest.fixture
def email_data():
    return {
        "recipients": ["foo@example.com"],
        "subject": "My email subject",
        "body": "Some text body",
        "tag": EmailTag.TEST,
    }


@pytest.fixture
def log_data():
    return {"tag": EmailTag.TEST, "sender_id": 123, "recipient_ids": [123]}


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.debug = False
    return pyramid_request


@pytest.fixture(autouse=True)
def celery(patch, pyramid_request):
    celery = patch("h.tasks.email.celery")
    celery.request = pyramid_request
    return celery
