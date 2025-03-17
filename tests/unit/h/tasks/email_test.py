from unittest import mock

import pytest

from h.services.email import EmailTag
from h.tasks import email


def test_send_retries_if_mailing_fails(email_service):
    email_service.send.side_effect = Exception()
    email.send.retry = mock.Mock(wraps=email.send.retry)

    data = {
        "recipients": ["foo@example.com"],
        "subject": "My email subject",
        "body": "Some text body",
        "tag": EmailTag.TEST,
    }
    with pytest.raises(Exception):  # noqa: B017, PT011
        email.send(data)

    assert email.send.retry.called


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.debug = False
    return pyramid_request


@pytest.fixture(autouse=True)
def celery(patch, pyramid_request):
    celery = patch("h.tasks.email.celery")
    celery.request = pyramid_request
    return celery
