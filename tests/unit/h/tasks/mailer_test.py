from smtplib import SMTPServerDisconnected
from unittest import mock

import pytest

from h.tasks import mailer


def test_send_retries_if_mailing_fails(email_service):
    email_service.send.side_effect = SMTPServerDisconnected()

    mailer.send.retry = mock.Mock(spec_set=[])
    mailer.send(
        recipients=["foo@example.com"],
        subject="My email subject",
        body="Some text body",
    )

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
