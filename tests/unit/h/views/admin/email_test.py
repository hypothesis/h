from dataclasses import asdict

import pytest
from pyramid.httpexceptions import HTTPSeeOther

from h.services.email import EmailData, EmailTag
from h.views.admin.email import email_index, email_test, preview_mention_notification


class TestEmailIndex:
    def test_when_no_taskid(self, pyramid_request):
        result = email_index(pyramid_request)

        assert result == {"taskid": None}

    def test_with_taskid(self, pyramid_request):
        pyramid_request.params["taskid"] = "abcd1234"

        result = email_index(pyramid_request)

        assert result == {"taskid": "abcd1234"}


@pytest.mark.usefixtures("email", "testmail", "routes")
class TestEmailTest:
    def test_doesnt_mail_when_no_recipient(self, email, pyramid_request):
        email_test(pyramid_request)

        assert not email.send.delay.called

    def test_redirects_when_no_recipient(self, pyramid_request):
        result = email_test(pyramid_request)

        assert isinstance(result, HTTPSeeOther)
        assert result.location == "/adm/email"

    def test_sends_mail(self, email, pyramid_request):
        pyramid_request.params["recipient"] = "meerkat@example.com"

        email_test(pyramid_request)

        email_data = EmailData(
            recipients=["meerkat@example.com"],
            subject="TEST",
            body="text",
            tag=EmailTag.TEST,
            html="html",
        )
        email.send.delay.assert_called_once_with(asdict(email_data))

    def test_redirects(self, pyramid_request):
        pyramid_request.params["recipient"] = "meerkat@example.com"

        result = email_test(pyramid_request)

        assert isinstance(result, HTTPSeeOther)
        assert result.location == "/adm/email?taskid=a1b2c3"


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
def email(patch):
    email = patch("h.views.admin.email.email")
    email.send.delay.return_value = FakeResult()
    return email


@pytest.fixture
def testmail(patch):
    test = patch("h.views.admin.email.test")
    test.generate.side_effect = lambda _, r: EmailData(
        recipients=[r], subject="TEST", body="text", tag=EmailTag.TEST, html="html"
    )
    return test


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("admin.email", "/adm/email")
