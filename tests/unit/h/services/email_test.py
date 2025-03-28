import smtplib
from unittest.mock import sentinel

import pytest

from h.services.email import EmailData, EmailService, EmailTag, LogData, factory


class TestEmailService:
    def test_send_creates_email_message(
        self, email_data, log_data, email_service, pyramid_mailer
    ):
        email_service.send(email_data, log_data)

        pyramid_mailer.message.Message.assert_called_once_with(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            html=None,
            extra_headers={"X-MC-Tags": EmailTag.TEST},
        )

    def test_send_creates_email_message_with_html_body(
        self, log_data, email_service, pyramid_mailer
    ):
        email = EmailData(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            tag=EmailTag.TEST,
            html="<p>An HTML body</p>",
        )
        email_service.send(email, log_data)

        pyramid_mailer.message.Message.assert_called_once_with(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            html="<p>An HTML body</p>",
            extra_headers={"X-MC-Tags": EmailTag.TEST},
        )

    def test_send_dispatches_email_using_request_mailer(
        self, email_data, log_data, email_service, pyramid_mailer
    ):
        request_mailer = pyramid_mailer.get_mailer.return_value
        message = pyramid_mailer.message.Message.return_value

        email_service.send(email_data, log_data)

        request_mailer.send_immediately.assert_called_once_with(message)

    def test_raises_smtplib_exception(
        self, email_data, log_data, email_service, pyramid_mailer
    ):
        request_mailer = pyramid_mailer.get_mailer.return_value
        request_mailer.send_immediately.side_effect = smtplib.SMTPException()

        with pytest.raises(smtplib.SMTPException):
            email_service.send(email_data, log_data)

    def test_send_logging(self, email_data, log_data, email_service, info_caplog):
        email_service.send(email_data, log_data)

        assert info_caplog.messages == [
            f"Sent email: tag={log_data.tag!r}, sender_id={log_data.sender_id}, recipient_ids={log_data.recipient_ids}"
        ]

    def test_send_logging_with_extra(self, email_data, email_service, info_caplog):
        user_id = 123
        annotation_id = "annotation_id"
        log_data = LogData(
            tag=email_data.tag,
            sender_id=user_id,
            recipient_ids=[user_id],
            extra={"annotation_id": annotation_id},
        )
        email_service.send(email_data, log_data)

        assert info_caplog.messages == [
            f"Sent email: tag={log_data.tag!r}, sender_id={user_id}, recipient_ids={[user_id]}, annotation_id={annotation_id!r}"
        ]

    @pytest.fixture
    def email_data(self):
        return EmailData(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            tag=EmailTag.TEST,
        )

    @pytest.fixture
    def log_data(self):
        return LogData(
            tag=EmailTag.TEST,
            sender_id=123,
            recipient_ids=[123],
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.debug = False
        return pyramid_request

    @pytest.fixture
    def email_service(self, pyramid_request, pyramid_mailer):
        request_mailer = pyramid_mailer.get_mailer.return_value
        return EmailService(pyramid_request, request_mailer)

    @pytest.fixture
    def info_caplog(self, caplog):
        caplog.set_level("INFO")
        return caplog


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
