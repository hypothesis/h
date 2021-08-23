import pytest

from h.emails.signup import generate


@pytest.mark.usefixtures("routes")
class TestGenerate:
    def test_calls_renderers_with_appropriate_context(
        self, pyramid_request, html_renderer, text_renderer
    ):
        generate(
            pyramid_request,
            user_id=1234,
            email="foo@example.com",
            activation_code="abcd4567",
        )

        expected_context = {
            "activate_link": "http://example.com/activate/1234/abcd4567"
        }
        html_renderer.assert_(**expected_context)
        text_renderer.assert_(**expected_context)

    def test_appropriate_return_values(
        self, pyramid_request, html_renderer, text_renderer
    ):
        html_renderer.string_response = "HTML output"
        text_renderer.string_response = "Text output"

        recipients, subject, text, html = generate(
            pyramid_request,
            user_id=1234,
            email="foo@example.com",
            activation_code="abcd4567",
        )

        assert recipients == ["foo@example.com"]
        assert subject == "Please activate your account"
        assert html == "HTML output"
        assert text == "Text output"

    def test_jinja_templates_render(self, pyramid_config, pyramid_request):
        """Ensure that the jinja templates don't contain syntax errors."""
        pyramid_config.include("pyramid_jinja2")
        pyramid_config.include("h.jinja_extensions")

        generate(
            pyramid_request,
            user_id=1234,
            email="foo@example.com",
            activation_code="abcd4567",
        )

    @pytest.fixture
    def html_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/signup.html.jinja2"
        )

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("activate", "/activate/{id}/{code}")

    @pytest.fixture
    def text_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/signup.txt.jinja2"
        )
