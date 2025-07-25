import pytest

from h import __version__
from h.emails.test import generate
from h.services.email import EmailData, EmailTag


class TestGenerate:
    def test_calls_renderers_with_appropriate_context(
        self, pyramid_request, html_renderer, text_renderer, matchers
    ):
        generate(pyramid_request, "meerkat@example.com")

        expected_context = {
            "time": matchers.InstanceOf(str),
            "hostname": matchers.InstanceOf(str),
            "python_version": matchers.InstanceOf(str),
            "version": __version__,
        }
        html_renderer.assert_(**expected_context)  # noqa: PT009
        text_renderer.assert_(**expected_context)  # noqa: PT009

    def test_appropriate_return_values(
        self, pyramid_request, html_renderer, text_renderer
    ):
        html_renderer.string_response = "HTML output"
        text_renderer.string_response = "Text output"

        email = generate(pyramid_request, "meerkat@example.com")

        assert email == EmailData(
            recipients=["meerkat@example.com"],
            subject="Test mail",
            body="Text output",
            html="HTML output",
            tag=EmailTag.TEST,
        )

    def test_jinja_templates_render(self, pyramid_config, pyramid_request):
        """Ensure that the jinja templates don't contain syntax errors"""  # noqa: D400, D415
        pyramid_config.include("pyramid_jinja2")

        generate(pyramid_request, "meerkat@example.com")

    @pytest.fixture
    def html_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/test.html.jinja2"
        )

    @pytest.fixture
    def text_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer("h:templates/emails/test.txt.jinja2")
