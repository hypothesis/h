from unittest import mock

import pytest

from h.emails.reset_password import generate


@pytest.mark.usefixtures("routes")
class TestGenerate:
    def test_calls_renderers_with_appropriate_context(
        self, pyramid_request, html_renderer, text_renderer, serializer, user
    ):
        pyramid_request.registry.password_reset_serializer = serializer

        generate(pyramid_request, user)

        expected_context = {
            "username": user.username,
            "reset_code": "s3cr3t-r3s3t-c0d3",
            "reset_link": "http://example.com/reset/s3cr3t-r3s3t-c0d3",
        }
        html_renderer.assert_(**expected_context)
        text_renderer.assert_(**expected_context)

    @pytest.mark.usefixtures("html_renderer", "text_renderer")
    def test_generates_token_using_username(self, pyramid_request, serializer, user):
        pyramid_request.registry.password_reset_serializer = serializer

        generate(pyramid_request, user)

        serializer.dumps.assert_called_once_with(user.username)

    def test_appropriate_return_values(
        self, pyramid_request, html_renderer, text_renderer, serializer, user
    ):
        pyramid_request.registry.password_reset_serializer = serializer

        html_renderer.string_response = "HTML output"
        text_renderer.string_response = "Text output"

        recipients, subject, text, html = generate(pyramid_request, user)

        assert recipients == [user.email]
        assert subject == "Reset your password"
        assert html == "HTML output"
        assert text == "Text output"

    def test_jinja_templates_render(
        self, pyramid_config, pyramid_request, serializer, user
    ):
        """Ensure that the jinja templates don't contain syntax errors."""
        pyramid_config.include("pyramid_jinja2")
        pyramid_request.registry.password_reset_serializer = serializer

        generate(pyramid_request, user)

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("account_reset_with_code", "/reset/{code}")

    @pytest.fixture
    def serializer(self):
        serializer = mock.Mock(spec_set=["dumps"])
        serializer.dumps.return_value = "s3cr3t-r3s3t-c0d3"
        return serializer

    @pytest.fixture
    def html_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/reset_password.html.jinja2"
        )

    @pytest.fixture
    def text_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/reset_password.txt.jinja2"
        )

    @pytest.fixture
    def user(self, factories):
        return factories.User()
