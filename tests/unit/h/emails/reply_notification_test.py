import datetime

import pytest

from h.emails.reply_notification import generate
from h.models import Annotation, Document, Subscriptions
from h.notification.reply import Notification


class TestGenerate:
    def test_it(
        self,
        notification,
        parent_user,
        pyramid_request,
        reply_user,
        html_renderer,
        text_renderer,
        links,
        subscription_service,
    ):
        generate(pyramid_request, notification)

        links.incontext_link.assert_called_once_with(
            pyramid_request, notification.reply
        )

        subscription_service.get_unsubscribe_token.assert_called_once_with(
            user_id=notification.parent_user.userid, type_=Subscriptions.Type.REPLY
        )

        expected_context = {
            "document_title": "My fascinating page",
            "document_url": "http://example.org/",
            "parent": notification.parent,
            "parent_user_display_name": parent_user.display_name,
            "parent_user_url": "http://example.com/stream/user/patricia",
            "reply": notification.reply,
            "reply_url": links.incontext_link.return_value,
            "reply_user_display_name": reply_user.display_name,
            "reply_user_url": "http://example.com/stream/user/ron",
            "unsubscribe_url": "http://example.com/unsub/FAKETOKEN",
        }
        html_renderer.assert_(**expected_context)
        text_renderer.assert_(**expected_context)

    def test_falls_back_to_target_uri_for_document_title(
        self, notification, pyramid_request, html_renderer, text_renderer
    ):
        notification.document.title = None

        generate(pyramid_request, notification)

        html_renderer.assert_(document_title="http://example.org/")
        text_renderer.assert_(document_title="http://example.org/")

    def test_falls_back_to_individual_page_if_no_bouncer(
        self,
        notification,
        parent_user,
        pyramid_request,
        reply_user,
        html_renderer,
        text_renderer,
        links,
    ):
        # It links to individual pages if bouncer isn't available.
        # If bouncer isn't enabled direct links in reply notification emails
        # should fall back to linking to the reply's individual page, instead of
        # the bouncer direct link.

        # incontext_link() returns None if bouncer isn't available.
        links.incontext_link.return_value = None

        generate(pyramid_request, notification)

        expected_context = {
            "document_title": "My fascinating page",
            "document_url": "http://example.org/",
            "parent": notification.parent,
            "parent_user_display_name": parent_user.display_name,
            "parent_user_url": "http://example.com/stream/user/patricia",
            "reply": notification.reply,
            "reply_url": "http://example.com/ann/bar456",
            "reply_user_display_name": reply_user.display_name,
            "reply_user_url": "http://example.com/stream/user/ron",
            "unsubscribe_url": "http://example.com/unsub/FAKETOKEN",
        }
        html_renderer.assert_(**expected_context)
        text_renderer.assert_(**expected_context)

    def test_supports_non_ascii_display_names(
        self,
        notification,
        pyramid_request,
        parent_user,
        reply_user,
    ):
        parent_user.display_name = "Parent 👩"
        reply_user.display_name = "Child 👧"

        (_, subject, _, _) = generate(pyramid_request, notification)

        assert subject == "Child 👧 has replied to your annotation"

    def test_returns_usernames_if_no_display_names(
        self,
        notification,
        pyramid_request,
        html_renderer,
        text_renderer,
        parent_user,
        reply_user,
    ):
        parent_user.display_name = None
        reply_user.display_name = None

        generate(pyramid_request, notification)

        expected_context = {
            "parent_user_display_name": parent_user.username,
            "reply_user_display_name": reply_user.username,
        }
        html_renderer.assert_(**expected_context)
        text_renderer.assert_(**expected_context)

    def test_returns_text_and_body_results_from_renderers(
        self, notification, pyramid_request, html_renderer, text_renderer
    ):
        html_renderer.string_response = "HTML output"
        text_renderer.string_response = "Text output"

        _, _, text, html = generate(pyramid_request, notification)

        assert html == "HTML output"
        assert text == "Text output"

    def test_returns_subject_with_reply_display_name(
        self, notification, pyramid_request
    ):
        _, subject, _, _ = generate(pyramid_request, notification)

        assert subject == "Ron Burgundy has replied to your annotation"

    def test_returns_subject_with_reply_username(
        self, notification, pyramid_request, reply_user
    ):
        reply_user.display_name = None
        _, subject, _, _ = generate(pyramid_request, notification)

        assert subject == "ron has replied to your annotation"

    def test_returns_parent_email_as_recipients(self, notification, pyramid_request):
        recipients, _, _, _ = generate(pyramid_request, notification)

        assert recipients == ["pat@ric.ia"]

    def test_jinja_templates_render(
        self, notification, pyramid_config, pyramid_request
    ):
        """Ensure that the jinja templates don't contain syntax errors."""
        pyramid_config.include("pyramid_jinja2")
        pyramid_config.include("h.jinja_extensions")

        generate(pyramid_request, notification)

    def test_urls_not_set_for_third_party_users(
        self, notification, pyramid_request, html_renderer, text_renderer
    ):
        pyramid_request.default_authority = "foo.org"
        expected_context = {"parent_user_url": None, "reply_user_url": None}

        generate(pyramid_request, notification)

        html_renderer.assert_(**expected_context)
        text_renderer.assert_(**expected_context)

    def test_urls_set_for_first_party_users(
        self, notification, pyramid_request, html_renderer, text_renderer
    ):
        expected_context = {
            "parent_user_url": "http://example.com/stream/user/patricia",
            "reply_user_url": "http://example.com/stream/user/ron",
        }

        generate(pyramid_request, notification)

        html_renderer.assert_(**expected_context)
        text_renderer.assert_(**expected_context)

    @pytest.fixture
    def document(self, db_session):
        doc = Document(title="My fascinating page")
        db_session.add(doc)
        db_session.flush()
        return doc

    @pytest.fixture
    def links(self, patch):
        return patch("h.emails.reply_notification.links")

    @pytest.fixture
    def notification(self, reply, reply_user, parent, parent_user, document):
        return Notification(
            reply=reply,
            reply_user=reply_user,
            parent=parent,
            parent_user=parent_user,
            document=document,
        )

    @pytest.fixture
    def parent(self):
        common = {
            "id": "foo123",
            "created": datetime.datetime.utcnow(),
            "updated": datetime.datetime.utcnow(),
            "text": "Foo is true",
        }
        return Annotation(target_uri="http://example.org/", **common)

    @pytest.fixture
    def parent_user(self, factories):
        return factories.User(
            username="patricia", email="pat@ric.ia", display_name="Patricia Demylus"
        )

    @pytest.fixture
    def reply(self):
        common = {
            "id": "bar456",
            "created": datetime.datetime.utcnow(),
            "updated": datetime.datetime.utcnow(),
            "text": "No it is not!",
        }
        return Annotation(target_uri="http://example.org/", **common)

    @pytest.fixture
    def reply_user(self, factories):
        return factories.User(
            username="ron", email="ron@thesmiths.com", display_name="Ron Burgundy"
        )

    @pytest.fixture(autouse=True)
    def subscription_service(self, subscription_service):
        subscription_service.get_unsubscribe_token.return_value = "FAKETOKEN"
        return subscription_service

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("annotation", "/ann/{id}")
        pyramid_config.add_route("stream.user_query", "/stream/user/{user}")
        pyramid_config.add_route("unsubscribe", "/unsub/{token}")

    @pytest.fixture(autouse=True)
    def html_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/reply_notification.html.jinja2"
        )

    @pytest.fixture(autouse=True)
    def text_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/reply_notification.txt.jinja2"
        )
