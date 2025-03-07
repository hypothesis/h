import pytest

from h.emails.flag_notification import generate
from h.services.email import EmailData, EmailTag


class TestGenerate:
    def test_calls_renderers_with_appropriate_context(
        self, pyramid_request, html_renderer, text_renderer
    ):
        generate(
            pyramid_request,
            email="foo@example.com",
            incontext_link="http://hyp.is/a/ann1",
        )

        expected_context = {"incontext_link": "http://hyp.is/a/ann1"}
        html_renderer.assert_(**expected_context)  # noqa: PT009
        text_renderer.assert_(**expected_context)  # noqa: PT009

    def test_appropriate_return_values(
        self, pyramid_request, html_renderer, text_renderer
    ):
        html_renderer.string_response = "HTML output"
        text_renderer.string_response = "Text output"

        email = generate(
            pyramid_request,
            email="foo@example.com",
            incontext_link="http://hyp.is/a/ann1",
        )

        assert email == EmailData(
            recipients=["foo@example.com"],
            subject="An annotation has been flagged",
            body="Text output",
            html="HTML output",
            tag=EmailTag.FLAG_NOTIFICATION,
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
