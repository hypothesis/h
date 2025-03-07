from unittest import mock

import pytest

from h.services.email import EmailData, EmailTag
from h.tasks import mailer


def test_send_retries_if_mailing_fails(email_service):
    email_service.send.side_effect = Exception()
    mailer.send.retry = mock.Mock(wraps=mailer.send.retry)

    with pytest.raises(Exception):  # noqa: B017, PT011
        mailer.send(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            tag=EmailTag.TEST,
        )

    assert mailer.send.retry.called


def test_send_retries_if_mailing_fails_with_email_data(email_service):
    email_service.send.side_effect = Exception()
    mailer.send.retry = mock.Mock(wraps=mailer.send.retry)

    email = EmailData(
        recipients=["foo@example.com"],
        subject="My email subject",
        body="Some text body",
        tag=EmailTag.TEST,
    )
    with pytest.raises(Exception):  # noqa: B017, PT011
        mailer.send(email)

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
