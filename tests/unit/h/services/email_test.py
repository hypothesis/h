import smtplib
from unittest.mock import sentinel

import pytest

from h.services.email import EmailData, EmailService, EmailTag, factory


class TestEmailService:
    def test_send_creates_email_message(self, email_service, pyramid_mailer):
        email = EmailData(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            tag=EmailTag.TEST,
        )
        email_service.send(email)

        pyramid_mailer.message.Message.assert_called_once_with(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            html=None,
            extra_headers={"X-MC-Tags": EmailTag.TEST},
        )

    def test_send_creates_email_message_with_html_body(
        self, email_service, pyramid_mailer
    ):
        email = EmailData(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            tag=EmailTag.TEST,
            html="<p>An HTML body</p>",
        )
        email_service.send(email)

        pyramid_mailer.message.Message.assert_called_once_with(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            html="<p>An HTML body</p>",
            extra_headers={"X-MC-Tags": EmailTag.TEST},
        )

    def test_send_dispatches_email_using_request_mailer(
        self, email_service, pyramid_mailer
    ):
        request_mailer = pyramid_mailer.get_mailer.return_value
        message = pyramid_mailer.message.Message.return_value

        email = EmailData(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            tag=EmailTag.TEST,
        )
        email_service.send(email)

        request_mailer.send_immediately.assert_called_once_with(message)

    def test_raises_smtplib_exception(self, email_service, pyramid_mailer):
        request_mailer = pyramid_mailer.get_mailer.return_value
        request_mailer.send_immediately.side_effect = smtplib.SMTPException()

        email = EmailData(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            tag=EmailTag.TEST,
        )
        with pytest.raises(smtplib.SMTPException):
            email_service.send(email)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.debug = False
        return pyramid_request

    @pytest.fixture
    def email_service(self, pyramid_request, pyramid_mailer):
        request_mailer = pyramid_mailer.get_mailer.return_value
        return EmailService(pyramid_request, request_mailer)


class TestFactory:
    def test_it(self, pyramid_request, pyramid_mailer, EmailService):
        service = factory(sentinel.context, pyramid_request)

        EmailService.assert_called_once_with(
            request=pyramid_request, mailer=pyramid_mailer.get_mailer.return_value
        )

        assert service == EmailService.return_value

    @pytest.fixture(autouse=True)
    def EmailService(self, patch):
        return patch("h.services.email.EmailService")


@pytest.fixture(autouse=True)
def pyramid_mailer(patch):
    return patch("h.services.email.pyramid_mailer", autospec=True)
