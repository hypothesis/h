import datetime

import pytest

from h.emails.mention_notification import generate
from h.models import Annotation, Document
from h.notification.mention import MentionNotification


class TestGenerate:
    def test_it(
        self,
        annotation,
        notification,
        document,
        mentioning_user,
        pyramid_request,
        html_renderer,
        text_renderer,
        links,
    ):
        app_url = "https://example.com"
        pyramid_request.registry.settings.update(
            {
                "h.app_url": app_url,
            }
        )

        generate(pyramid_request, notification)

        links.incontext_link.assert_called_once_with(
            pyramid_request, notification.annotation
        )

        expected_context = {
            "username": mentioning_user.username,
            "user_display_name": mentioning_user.display_name,
            "annotation_url": links.incontext_link.return_value,
            "document_title": document.title,
            "document_url": annotation.target_uri,
            "annotation": notification.annotation,
            "annotation_quote": "quoted text",
            "app_url": app_url,
        }
        html_renderer.assert_(**expected_context)  # noqa: PT009
        text_renderer.assert_(**expected_context)  # noqa: PT009

    def test_falls_back_to_individual_page_if_no_bouncer(
        self,
        annotation,
        notification,
        pyramid_request,
        html_renderer,
        text_renderer,
        links,
    ):
        links.incontext_link.return_value = None

        generate(pyramid_request, notification)

        expected_context = {
            "annotation_url": f"http://example.com/ann/{annotation.id}",
        }
        html_renderer.assert_(**expected_context)  # noqa: PT009
        text_renderer.assert_(**expected_context)  # noqa: PT009

    def test_returns_usernames_if_no_display_names(
        self,
        notification,
        mentioning_user,
        pyramid_request,
        html_renderer,
        text_renderer,
    ):
        mentioning_user.display_name = None

        generate(pyramid_request, notification)

        expected_context = {
            "user_display_name": f"@{mentioning_user.username}",
        }
        html_renderer.assert_(**expected_context)  # noqa: PT009
        text_renderer.assert_(**expected_context)  # noqa: PT009

    def test_returns_text_and_body_results_from_renderers(
        self, notification, pyramid_request, html_renderer, text_renderer
    ):
        html_renderer.string_response = "HTML output"
        text_renderer.string_response = "Text output"

        email = generate(pyramid_request, notification)

        assert email.body == "Text output"
        assert email.html == "HTML output"

    def test_returns_subject_with_document_title(
        self, document, notification, pyramid_request
    ):
        email = generate(pyramid_request, notification)

        assert email.subject == f"You have been mentioned in {document.title}"

    def test_returns_parent_email_as_recipients(
        self, notification, pyramid_request, mentioned_user
    ):
        email = generate(pyramid_request, notification)

        assert email.recipients == [mentioned_user.email]

    def test_jinja_templates_render(
        self, notification, pyramid_config, pyramid_request
    ):
        """Ensure that the jinja templates don't contain syntax errors."""
        pyramid_config.include("pyramid_jinja2")
        pyramid_config.include("h.jinja_extensions")

        # Mock asset_url jinja global only for this test
        environment = pyramid_config.get_jinja2_environment()
        environment.globals["asset_url"] = lambda url: url

        generate(pyramid_request, notification)

    @pytest.fixture
    def notification(self, mentioning_user, mentioned_user, annotation, document):
        return MentionNotification(
            mentioning_user=mentioning_user,
            mentioned_user=mentioned_user,
            annotation=annotation,
            document=document,
        )

    @pytest.fixture
    def document(self, db_session):
        doc = Document(title="My fascinating page")
        db_session.add(doc)
        db_session.flush()
        return doc

    @pytest.fixture
    def mentioning_user(self, factories):
        return factories.User()

    @pytest.fixture
    def mentioned_user(self, factories):
        return factories.User()

    @pytest.fixture
    def annotation(self):
        common = {
            "id": "foo123",
            "created": datetime.datetime.now(tz=datetime.UTC),
            "updated": datetime.datetime.now(tz=datetime.UTC),
            "text": "Foo is true",
        }
        return Annotation(
            target_uri="http://example.org/",
            target_selectors=[{"type": "TextQuoteSelector", "exact": "quoted text"}],
            **common,
        )

    @pytest.fixture(autouse=True)
    def links(self, patch):
        return patch("h.emails.mention_notification.links")

    @pytest.fixture(autouse=True)
    def html_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/mention_notification.html.jinja2"
        )

    @pytest.fixture(autouse=True)
    def text_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/mention_notification.txt.jinja2"
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
        pyramid_config.add_route(
            "account_notifications", "/account/settings/notifications"
        )
