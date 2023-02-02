import pytest
from h_matchers import Any

from h import __version__
from h.emails.test import generate


class TestGenerate:
    def test_calls_renderers_with_appropriate_context(
        self, pyramid_request, html_renderer, text_renderer
    ):
        generate(pyramid_request, "meerkat@example.com")

        expected_context = {
            "time": Any.string(),
            "hostname": Any.string(),
            "python_version": Any.string(),
            "version": __version__,
        }
        html_renderer.assert_(**expected_context)
        text_renderer.assert_(**expected_context)

    def test_appropriate_return_values(
        self, pyramid_request, html_renderer, text_renderer
    ):
        html_renderer.string_response = "HTML output"
        text_renderer.string_response = "Text output"

        recipients, subject, text, html = generate(
            pyramid_request, "meerkat@example.com"
        )

        assert recipients == ["meerkat@example.com"]
        assert subject == "Test mail"
        assert html == "HTML output"
        assert text == "Text output"

    def test_jinja_templates_render(self, pyramid_config, pyramid_request):
        """Ensure that the jinja templates don't contain syntax errors"""
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
