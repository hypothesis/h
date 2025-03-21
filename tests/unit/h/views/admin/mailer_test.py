from dataclasses import asdict
from unittest.mock import create_autospec

import pytest
from pyramid.httpexceptions import HTTPSeeOther

from h.services.email import EmailData, EmailTag, LogData
from h.tasks import mailer
from h.views.admin.mailer import mailer_index, mailer_test, preview_mention_notification


class TestMailerIndex:
    def test_when_no_taskid(self, pyramid_request):
        result = mailer_index(pyramid_request)

        assert result == {"taskid": None}

    def test_with_taskid(self, pyramid_request):
        pyramid_request.params["taskid"] = "abcd1234"

        result = mailer_index(pyramid_request)

        assert result == {"taskid": "abcd1234"}


@pytest.mark.usefixtures("tasks_mailer", "testmail", "routes")
class TestMailerTest:
    def test_doesnt_mail_when_no_recipient(self, tasks_mailer, pyramid_request):
        mailer_test(pyramid_request)

        assert not tasks_mailer.send.delay.called

    def test_redirects_when_no_recipient(self, pyramid_request):
        result = mailer_test(pyramid_request)

        assert isinstance(result, HTTPSeeOther)
        assert result.location == "/adm/mailer"

    def test_sends_mail(self, tasks_mailer, pyramid_request, user):
        pyramid_request.params["recipient"] = "meerkat@example.com"

        mailer_test(pyramid_request)

        email_data = EmailData(
            recipients=["meerkat@example.com"],
            subject="TEST",
            body="text",
            tag=EmailTag.TEST,
            html="html",
        )
        log_data = LogData(tag=email_data.tag, sender_id=user.id)
        tasks_mailer.send.delay.assert_called_once_with(
            asdict(email_data), asdict(log_data)
        )

    def test_redirects(self, pyramid_request):
        pyramid_request.params["recipient"] = "meerkat@example.com"

        result = mailer_test(pyramid_request)

        assert isinstance(result, HTTPSeeOther)
        assert result.location == "/adm/mailer?taskid=a1b2c3"

    @pytest.fixture
    def user(self, factories, db_session):
        user = factories.User.create()
        db_session.commit()
        return user

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.user = user
        return pyramid_request


class TestPreviewMentionNotification:
    def test_returns_dummy_data(self, pyramid_request):
        result = preview_mention_notification(pyramid_request)

        assert result == {
            "username": "janedoe",
            "user_display_name": "Jane Doe",
            "annotation_url": "https://example.com/bouncer",
            "document_title": "The document",
            "document_url": "https://example.com/document",
            "annotation": {
                "text_rendered": 'Hello <a data-hyp-mention data-userid="acct:user@example.com">@user</a>, how are you?',
            },
            "annotation_quote": "This is a very important text",
        }


class FakeResult:
    def __init__(self):
        self.task_id = "a1b2c3"


@pytest.fixture
def tasks_mailer(patch):
    mock = patch("h.views.admin.mailer.mailer")
    mock.send.delay = create_autospec(mailer.send.run, return_value=FakeResult())
    return mock


@pytest.fixture
def testmail(patch):
    test = patch("h.views.admin.mailer.test")
    test.generate.side_effect = lambda _, r: EmailData(
        recipients=[r], subject="TEST", body="text", tag=EmailTag.TEST, html="html"
    )
    return test


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("admin.mailer", "/adm/mailer")
