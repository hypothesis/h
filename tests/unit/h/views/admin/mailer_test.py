from dataclasses import asdict

import pytest
from pyramid.httpexceptions import HTTPSeeOther

from h.services.email import EmailData, EmailTag
from h.views.admin.mailer import mailer_index, mailer_test, preview_mention_notification


class TestMailerIndex:
    def test_when_no_taskid(self, pyramid_request):
        result = mailer_index(pyramid_request)

        assert result == {"taskid": None}

    def test_with_taskid(self, pyramid_request):
        pyramid_request.params["taskid"] = "abcd1234"

        result = mailer_index(pyramid_request)

        assert result == {"taskid": "abcd1234"}


@pytest.mark.usefixtures("mailer", "testmail", "routes")
class TestMailerTest:
    def test_doesnt_mail_when_no_recipient(self, mailer, pyramid_request):
        mailer_test(pyramid_request)

        assert not mailer.send.delay.called

    def test_redirects_when_no_recipient(self, pyramid_request):
        result = mailer_test(pyramid_request)

        assert isinstance(result, HTTPSeeOther)
        assert result.location == "/adm/mailer"

    def test_sends_mail(self, mailer, pyramid_request):
        pyramid_request.params["recipient"] = "meerkat@example.com"

        mailer_test(pyramid_request)

        email = EmailData(
            recipients=["meerkat@example.com"],
            subject="TEST",
            body="text",
            tag=EmailTag.TEST,
            html="html",
        )
        mailer.send.delay.assert_called_once_with(asdict(email))

    def test_redirects(self, pyramid_request):
        pyramid_request.params["recipient"] = "meerkat@example.com"

        result = mailer_test(pyramid_request)

        assert isinstance(result, HTTPSeeOther)
        assert result.location == "/adm/mailer?taskid=a1b2c3"


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
def mailer(patch):
    mailer = patch("h.views.admin.mailer.mailer")
    mailer.send.delay.return_value = FakeResult()
    return mailer


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
