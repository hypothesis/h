from dataclasses import asdict
from unittest.mock import create_autospec

import pytest
from pyramid.httpexceptions import HTTPSeeOther

from h.services.email import EmailData, EmailTag, TaskData
from h.tasks import email
from h.views.admin.email import (
    email_index,
    email_test,
    preview_annotation_moderation_notification,
    preview_mention_notification,
)


class TestEmailIndex:
    def test_when_no_taskid(self, pyramid_request):
        result = email_index(pyramid_request)

        assert result == {"taskid": None}

    def test_with_taskid(self, pyramid_request):
        pyramid_request.params["taskid"] = "abcd1234"

        result = email_index(pyramid_request)

        assert result == {"taskid": "abcd1234"}


@pytest.mark.usefixtures("tasks_email", "testmail", "routes")
class TestEmailTest:
    def test_doesnt_mail_when_no_recipient(self, tasks_email, pyramid_request):
        email_test(pyramid_request)

        assert not tasks_email.send.delay.called

    def test_redirects_when_no_recipient(self, pyramid_request):
        result = email_test(pyramid_request)

        assert isinstance(result, HTTPSeeOther)
        assert result.location == "/adm/email"

    def test_sends_mail(self, tasks_email, pyramid_request, user):
        pyramid_request.params["recipient"] = "meerkat@example.com"

        email_test(pyramid_request)

        email_data = EmailData(
            recipients=["meerkat@example.com"],
            subject="TEST",
            body="text",
            tag=EmailTag.TEST,
            html="html",
        )
        task_data = TaskData(tag=email_data.tag, sender_id=user.id)
        tasks_email.send.delay.assert_called_once_with(
            asdict(email_data), asdict(task_data)
        )

    def test_redirects(self, pyramid_request):
        pyramid_request.params["recipient"] = "meerkat@example.com"

        result = email_test(pyramid_request)

        assert isinstance(result, HTTPSeeOther)
        assert result.location == "/adm/email?taskid=a1b2c3"

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


class TestPreviewModeratedAnnotationNotification:
    def test_returns_dummy_data(self, pyramid_request):
        result = preview_annotation_moderation_notification(pyramid_request)

        assert result == {
            "user_display_name": "Jane Doe",
            "status_change_description": "The following comment has been approved by the moderation team for GROUP NAME.\nIt's now visible to everyone viewing that group.",
            "annotation_url": "https://example.com/bouncer",
            "annotation": {
                "text_rendered": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla tincidunt malesuada ex, id dictum risus posuere sed. Curabitur risus lectus, aliquam vel tempus ut, tempus non risus. Duis ac nibh lacinia, lacinia leo sit amet, lacinia tortor. Vestibulum dictum maximus lorem, nec lobortis augue ullamcorper nec. Ut ac viverra nisi. Nam congue neque eu mi viverra ultricies. Integer pretium odio nulla, at semper dolor tincidunt quis. Pellentesque suscipit magna nec nunc mollis, a interdum purus aliquam.",
            },
            "annotation_quote": "This is a very important text",
        }


class FakeResult:
    def __init__(self):
        self.task_id = "a1b2c3"


@pytest.fixture
def tasks_email(patch):
    mock = patch("h.views.admin.email.email")
    mock.send.delay = create_autospec(email.send.run, return_value=FakeResult())
    return mock


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
