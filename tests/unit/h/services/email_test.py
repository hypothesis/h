import smtplib
from unittest import mock
from unittest.mock import sentinel

import pytest

from h.services.email import (
    DAILY_SENDER_MENTION_LIMIT,
    EmailData,
    EmailService,
    EmailTag,
    TaskData,
    factory,
)


class TestEmailService:
    def test_send_creates_email_message(
        self, email_data, task_data, email_service, pyramid_mailer
    ):
        email_service.send(email_data, task_data)

        pyramid_mailer.message.Message.assert_called_once_with(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            html=None,
            extra_headers={"X-MC-Tags": EmailTag.TEST},
        )

    def test_send_creates_email_message_with_html_body(
        self, email_service, task_data, pyramid_mailer
    ):
        email_data = EmailData(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            tag=EmailTag.TEST,
            html="<p>An HTML body</p>",
        )

        email_service.send(email_data, task_data)

        pyramid_mailer.message.Message.assert_called_once_with(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            html="<p>An HTML body</p>",
            extra_headers={"X-MC-Tags": EmailTag.TEST},
        )

    def test_send_creates_email_message_with_subaccount(
        self, task_data, email_service, pyramid_mailer
    ):
        email = EmailData(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            tag=EmailTag.TEST,
            subaccount="subaccount",
        )
        email_service.send(email, task_data)

        pyramid_mailer.message.Message.assert_called_once_with(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            html=None,
            extra_headers={"X-MC-Tags": EmailTag.TEST, "X-MC-Subaccount": "subaccount"},
        )

    def test_send_creates_mention_email_when_sender_limit_not_reached(
        self,
        mention_email_data,
        mention_task_data,
        email_service,
        pyramid_mailer,
        task_done_service,
    ):
        task_done_service.sender_mention_count.return_value = (
            DAILY_SENDER_MENTION_LIMIT - 1
        )

        email_service.send(mention_email_data, mention_task_data)

        task_done_service.sender_mention_count.assert_called_once_with(
            mention_task_data.sender_id, mock.ANY
        )
        pyramid_mailer.message.Message.assert_called_once_with(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            html=None,
            extra_headers={"X-MC-Tags": EmailTag.MENTION_NOTIFICATION},
        )

    def test_send_does_not_create_mention_email_when_sender_limit_reached(
        self,
        mention_email_data,
        mention_task_data,
        email_service,
        pyramid_mailer,
        task_done_service,
    ):
        task_done_service.sender_mention_count.return_value = DAILY_SENDER_MENTION_LIMIT

        email_service.send(mention_email_data, mention_task_data)

        task_done_service.sender_mention_count.assert_called_once_with(
            mention_task_data.sender_id, mock.ANY
        )
        pyramid_mailer.message.Message.assert_not_called()

    def test_send_dispatches_email_using_request_mailer(
        self, email_data, task_data, email_service, pyramid_mailer
    ):
        request_mailer = pyramid_mailer.get_mailer.return_value
        message = pyramid_mailer.message.Message.return_value

        email_service.send(email_data, task_data)

        request_mailer.send_immediately.assert_called_once_with(message)

    def test_raises_smtplib_exception(
        self, email_data, task_data, email_service, pyramid_mailer
    ):
        request_mailer = pyramid_mailer.get_mailer.return_value
        request_mailer.send_immediately.side_effect = smtplib.SMTPException()

        with pytest.raises(smtplib.SMTPException):
            email_service.send(email_data, task_data)

    def test_send_logging(self, email_data, task_data, email_service, info_caplog):
        email_service.send(email_data, task_data)

        assert info_caplog.messages == [
            f"Sent email: tag={task_data.tag!r}, sender_id={task_data.sender_id}, recipient_ids={task_data.recipient_ids}"
        ]

    def test_send_logging_with_extra(self, email_data, email_service, info_caplog):
        sender_id = 123
        recipient_id = 124
        annotation_id = "annotation_id"
        task_data = TaskData(
            tag=email_data.tag,
            sender_id=sender_id,
            recipient_ids=[recipient_id],
            extra={"annotation_id": annotation_id},
        )

        email_service.send(email_data, task_data)

        assert info_caplog.messages == [
            f"Sent email: tag={task_data.tag!r}, sender_id={sender_id}, recipient_ids={[recipient_id]}, annotation_id={annotation_id!r}"
        ]

    def test_sender_limit_reached_logging(
        self,
        mention_email_data,
        mention_task_data,
        email_service,
        task_done_service,
        info_caplog,
    ):
        task_done_service.sender_mention_count.return_value = DAILY_SENDER_MENTION_LIMIT

        email_service.send(mention_email_data, mention_task_data)

        assert info_caplog.messages == [
            f"Not sending email: tag={mention_task_data.tag!r} sender_id={mention_task_data.sender_id} recipient_ids={mention_task_data.recipient_ids}. Sender limit reached."
        ]

    def test_send_creates_task_done(
        self, email_data, task_data, email_service, task_done_service
    ):
        task_data = TaskData(
            tag=email_data.tag,
            sender_id=123,
            recipient_ids=[124],
            extra={"annotation_id": "annotation_id"},
        )

        email_service.send(email_data, task_data)

        task_done_service.create.assert_called_once_with(task_data)

    @pytest.fixture
    def email_data(self):
        return EmailData(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            tag=EmailTag.TEST,
        )

    @pytest.fixture
    def task_data(self):
        return TaskData(
            tag=EmailTag.TEST,
            sender_id=123,
            recipient_ids=[124],
        )

    @pytest.fixture
    def mention_email_data(self):
        return EmailData(
            recipients=["foo@example.com"],
            subject="My email subject",
            body="Some text body",
            tag=EmailTag.MENTION_NOTIFICATION,
        )

    @pytest.fixture
    def mention_task_data(self):
        return TaskData(
            tag=EmailTag.MENTION_NOTIFICATION,
            sender_id=123,
            recipient_ids=[124],
        )

    @pytest.fixture
    def email_service(self, pyramid_request, pyramid_mailer, task_done_service):
        request_mailer = pyramid_mailer.get_mailer.return_value
        return EmailService(
            debug=pyramid_request.debug,
            session=pyramid_request.db,
            mailer=request_mailer,
            task_done_service=task_done_service,
        )

    @pytest.fixture
    def info_caplog(self, caplog):
        caplog.set_level("INFO")
        return caplog


class TestFactory:
    def test_it(self, pyramid_request, pyramid_mailer, EmailService, task_done_service):
        service = factory(sentinel.context, pyramid_request)

        EmailService.assert_called_once_with(
            debug=pyramid_request.debug,
            session=pyramid_request.db,
            mailer=pyramid_mailer.get_mailer.return_value,
            task_done_service=task_done_service,
        )

        assert service == EmailService.return_value

    @pytest.fixture(autouse=True)
    def EmailService(self, patch):
        return patch("h.services.email.EmailService")


@pytest.fixture(autouse=True)
def pyramid_mailer(patch):
    return patch("h.services.email.pyramid_mailer", autospec=True)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.debug = False
    return pyramid_request
