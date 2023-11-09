from unittest import mock

import pytest
from h_matchers import Any

from h import form


class TestJinja2Renderer:
    def test_call_fetches_correct_templates(self, jinja2_env):
        renderer = form.Jinja2Renderer(jinja2_env)

        renderer("foo")
        renderer("foo.jinja2")
        renderer("bar/baz")
        renderer("bar/baz.jinja2")

        assert jinja2_env.get_template.call_args_list == [
            mock.call("foo.jinja2"),
            mock.call("foo.jinja2"),
            mock.call("bar/baz.jinja2"),
            mock.call("bar/baz.jinja2"),
        ]

    def test_call_passes_kwargs_to_render(self, jinja2_env, jinja2_template):
        renderer = form.Jinja2Renderer(jinja2_env)

        renderer("textinput", foo="foo", bar="bar")

        jinja2_template.render.assert_called_once_with({"foo": "foo", "bar": "bar"})

    def test_call_passes_system_context_to_render(self, jinja2_env, jinja2_template):
        renderer = form.Jinja2Renderer(jinja2_env, {"bar": "default"})

        renderer("textinput")
        renderer("textinput", foo="foo")
        renderer("textinput", foo="foo", bar="bar")

        assert jinja2_template.render.call_args_list == [
            mock.call({"bar": "default"}),
            mock.call({"foo": "foo", "bar": "default"}),
            mock.call({"foo": "foo", "bar": "bar"}),
        ]

    @pytest.fixture
    def jinja2_env(self, jinja2_template):
        environment = mock.Mock(spec_set=["get_template"])
        environment.get_template.return_value = jinja2_template
        return environment

    @pytest.fixture
    def jinja2_template(self):
        return mock.Mock(spec_set=["render"])


class TestCreateEnvironment:
    def test_overlays_base_with_correct_args(self):
        base = mock.Mock(spec_set=["overlay"])

        form.create_environment(base)

        base.overlay.assert_called_once_with(autoescape=True, loader=Any())

    def test_loader_has_correct_paths(self):
        base = mock.Mock(spec_set=["overlay"])

        form.create_environment(base)
        _, kwargs = base.overlay.call_args
        loader = kwargs["loader"]

        assert "templates/deform" in loader.searchpath[0]


class TestCreateForm:
    def test_returns_form_object(self, Form, pyramid_request):
        result = form.create_form(pyramid_request, mock.sentinel.schema)

        assert result == Form.return_value

    def test_passes_args_including_renderer_to_form_ctor(self, Form, pyramid_request):
        form.create_form(pyramid_request, mock.sentinel.schema, foo="bar")

        Form.assert_called_once_with(
            mock.sentinel.schema,
            foo="bar",
            renderer=Any.instance_of(form.Jinja2Renderer),
        )

    def test_adds_feature_client_to_system_context(self, patch, pyramid_request):
        Jinja2Renderer = patch("h.form.Jinja2Renderer")

        form.create_form(pyramid_request, mock.sentinel.schema)

        Jinja2Renderer.assert_called_once_with(
            mock.sentinel.jinja2_env, {"feature": pyramid_request.feature}
        )

    @pytest.fixture(autouse=True)
    def Form(self, patch):
        return patch("deform.Form")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.registry[form.ENVIRONMENT_KEY] = mock.sentinel.jinja2_env
        return pyramid_request


class TestToXHRResponse:
    """Unit tests for to_xhr_response()."""

    def test_returns_given_result_if_not_xhr(self, pyramid_request):
        """
        If ``request`` isn't an XHR request it returns ``non_xhr_result``.

        The calling view callable passes in the result that it would have
        returned normally if this were not an XHR request as the
        ``non_xhr_result`` argument. If the given ``request`` is not an XHR
        request then ``non_xhr_result`` should just be returned unmodified.

        """
        pyramid_request.is_xhr = False

        result = form.to_xhr_response(
            pyramid_request, mock.sentinel.non_xhr_result, mock.sentinel.form
        )

        assert result == mock.sentinel.non_xhr_result

    def test_returns_form_if_xhr(self, pyramid_request):
        """
        If ``request`` is an XHR request it should return the rendered ``form``.

        It should return ``form`` rendered to a ``<form>`` element HTML snippet.

        """
        pyramid_request.is_xhr = True
        form_ = mock.Mock(spec_set=["render"])

        result = form.to_xhr_response(
            pyramid_request, mock.sentinel.non_xhr_result, form_
        )

        assert result == form_.render.return_value

    def test_does_not_show_flash_message_if_xhr(self, pyramid_request):
        pyramid_request.is_xhr = True
        form_ = mock.Mock(spec_set=["render"])

        form.to_xhr_response(pyramid_request, mock.sentinel.non_xhr_result, form_)

        assert pyramid_request.session.peek_flash("success") == []


@pytest.mark.usefixtures("to_xhr_response")
class TestHandleFormSubmission:
    def test_it_calls_validate(self, pyramid_request):
        form_ = mock.Mock(spec_set=["validate"])

        form.handle_form_submission(
            pyramid_request, form_, mock_callable(), mock.sentinel.on_failure
        )

        post_items = Any.iterable.containing(list(pyramid_request.POST.items())).only()
        form_.validate.assert_called_once_with(post_items)

    def test_if_validation_fails_it_calls_on_failure(
        self, pyramid_request, invalid_form
    ):
        on_failure = mock_callable()

        form.handle_form_submission(
            pyramid_request, invalid_form(), mock.sentinel.on_success, on_failure
        )

        on_failure.assert_called_once_with()

    def test_if_validation_fails_it_calls_to_xhr_response(
        self, invalid_form, pyramid_request, to_xhr_response
    ):
        on_failure = mock_callable()
        form_ = invalid_form()

        form.handle_form_submission(
            pyramid_request, form_, mock.sentinel.on_success, on_failure
        )

        to_xhr_response.assert_called_once_with(
            pyramid_request, on_failure.return_value, form_
        )

    def test_if_validation_fails_it_sets_response_status_to_400(
        self, invalid_form, pyramid_request, to_xhr_response
    ):
        form.handle_form_submission(
            pyramid_request, invalid_form(), mock.sentinel.on_success, mock_callable()
        )

        assert to_xhr_response.call_args[0][0].response.status_int == 400

    def test_if_validation_fails_it_returns_to_xhr_response(
        self, invalid_form, pyramid_request, to_xhr_response
    ):
        result = form.handle_form_submission(
            pyramid_request, invalid_form(), mock.sentinel.on_success, mock_callable()
        )

        assert result == to_xhr_response.return_value

    def test_if_validation_succeeds_it_calls_on_success(
        self, form_validating_to, pyramid_request
    ):
        form_ = form_validating_to(mock.sentinel.appstruct)
        on_success = mock_callable()

        form.handle_form_submission(
            pyramid_request, form_, on_success, mock.sentinel.on_failure
        )

        on_success.assert_called_once_with(mock.sentinel.appstruct)

    def test_if_validation_succeeds_it_shows_a_flash_message(
        self, form_validating_to, pyramid_request
    ):
        form.handle_form_submission(
            pyramid_request,
            form_validating_to("anything"),
            mock_callable(),
            mock.sentinel.on_failure,
        )

        assert pyramid_request.session.peek_flash("success")

    def test_if_validation_succeeds_it_calls_to_xhr_response(
        self, form_validating_to, matchers, pyramid_request, to_xhr_response
    ):
        form_ = form_validating_to("anything")

        form.handle_form_submission(
            pyramid_request,
            form_,
            mock_callable(return_value=None),
            mock.sentinel.on_failure,
        )

        to_xhr_response.assert_called_once_with(
            pyramid_request, matchers.Redirect302To(pyramid_request.url), form_
        )

    def test_if_validation_succeeds_it_passes_on_success_result_to_to_xhr_response(
        self, form_validating_to, pyramid_request, to_xhr_response
    ):
        """
        A result from on_success() is passed to to_xhr_response().

        If on_success() returns something other than None, it passes that
        something to to_xhr_response().

        """
        form_ = form_validating_to("anything")

        form.handle_form_submission(
            pyramid_request,
            form_,
            mock_callable(return_value=mock.sentinel.result),
            mock.sentinel.on_failure,
        )

        to_xhr_response.assert_called_once_with(
            pyramid_request, mock.sentinel.result, form_
        )

    def test_if_validation_succeeds_it_returns_to_xhr_response(
        self, form_validating_to, pyramid_request, to_xhr_response
    ):
        result = form.handle_form_submission(
            pyramid_request,
            form_validating_to("anything"),
            mock_callable(),
            mock.sentinel.on_failure,
        )

        assert result == to_xhr_response.return_value

    @pytest.fixture
    def to_xhr_response(self, patch):
        return patch("h.form.to_xhr_response")


def mock_callable(**kwargs):
    """
    Return a mock than can be called but doesn't have any accessible properties.

    The mock can be called like ``my_mock_callable()`` but trying to access any
    other properties like ``my_mock_callable.foo`` will fail. This is a useful
    value to use when the method under test requires a callable as an argument.

    """
    return mock.Mock(spec_set=["__call__"], **kwargs)
