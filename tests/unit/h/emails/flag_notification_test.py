import pytest

from h.emails.flag_notification import generate
from h.services.email import EmailLogData, EmailTag


class TestGenerate:
    def test_calls_renderers_with_appropriate_context(
        self, pyramid_request, html_renderer, text_renderer, factories
    ):
        generate(
            pyramid_request,
            [factories.User.build()],
            incontext_link="http://hyp.is/a/ann1",
            annotation_id="ann1",
        )

        expected_context = {"incontext_link": "http://hyp.is/a/ann1"}
        html_renderer.assert_(**expected_context)  # noqa: PT009
        text_renderer.assert_(**expected_context)  # noqa: PT009

    def test_appropriate_return_values(
        self, pyramid_request, html_renderer, text_renderer, factories
    ):
        html_renderer.string_response = "HTML output"
        text_renderer.string_response = "Text output"

        annotation_id = "ann1"
        users = [factories.User.build(email="foo@example.com")]
        recipients, subject, text, tag, html, log_data = generate(
            pyramid_request,
            users,
            incontext_link=f"http://hyp.is/a/{annotation_id}",
            annotation_id=annotation_id,
        )

        assert recipients == [user.email for user in users]
        assert subject == "An annotation has been flagged"
        assert html == "HTML output"
        assert tag == EmailTag.FLAG_NOTIFICATION
        assert text == "Text output"
        assert log_data == EmailLogData(
            tag=EmailTag.FLAG_NOTIFICATION,
            recipient_ids=[user.id for user in users],
            annotation_id=annotation_id,
        )

    @pytest.fixture
    def html_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/flag_notification.html.jinja2"
        )

    @pytest.fixture
    def text_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/flag_notification.txt.jinja2"
        )
