import datetime

import pytest

from h.emails.mention_notification import generate
from h.emails.util import get_user_url
from h.models import Annotation, Document
from h.notification.mention import Notification


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
        generate(pyramid_request, notification)

        links.incontext_link.assert_called_once_with(
            pyramid_request, notification.annotation
        )

        expected_context = {
            "user_url": get_user_url(notification.mentioning_user, pyramid_request),
            "user_display_name": mentioning_user.display_name,
            "annotation_url": links.incontext_link.return_value,
            "document_title": document.title,
            "document_url": annotation.target_uri,
            "annotation": notification.annotation,
        }
        html_renderer.assert_(**expected_context)  # noqa: PT009
        text_renderer.assert_(**expected_context)  # noqa: PT009

    def test_falls_back_to_individual_page_if_no_bouncer(
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
        links.incontext_link.return_value = None

        generate(pyramid_request, notification)

        expected_context = {
            "annotation_url": f"http://example.com/ann/{annotation.id}",
        }
        html_renderer.assert_(**expected_context)  # noqa: PT009
        text_renderer.assert_(**expected_context)  # noqa: PT009

    def test_returns_usernames_if_no_display_names(
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
        mentioning_user.display_name = None

        generate(pyramid_request, notification)

        expected_context = {
            "user_display_name": mentioning_user.username,
        }
        html_renderer.assert_(**expected_context)  # noqa: PT009
        text_renderer.assert_(**expected_context)  # noqa: PT00

    def test_returns_text_and_body_results_from_renderers(
        self, notification, pyramid_request, html_renderer, text_renderer
    ):
        html_renderer.string_response = "HTML output"
        text_renderer.string_response = "Text output"

        _, _, text, html = generate(pyramid_request, notification)

        assert html == "HTML output"
        assert text == "Text output"

    @pytest.fixture
    def notification(self, mentioning_user, mentioned_user, annotation, document):
        return Notification(
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
        return factories.User(
            username="patricia", email="pat@ric.ia", display_name="Patricia Demylus"
        )

    @pytest.fixture
    def mentioned_user(self, factories):
        return factories.User(
            username="ron", email="ron@thesmiths.com", display_name="Ron Burgundy"
        )

    @pytest.fixture
    def annotation(self):
        common = {
            "id": "foo123",
            "created": datetime.datetime.now(tz=datetime.UTC),
            "updated": datetime.datetime.now(tz=datetime.UTC),
            "text": "Foo is true",
        }
        return Annotation(target_uri="http://example.org/", **common)

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
    def routes(self, pyramid_config):
        pyramid_config.add_route("annotation", "/ann/{id}")
        pyramid_config.add_route("stream.user_query", "/stream/user/{user}")
