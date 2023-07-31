from unittest.mock import Mock

import pytest

from h.util.view import handle_exception, json_view


class TestHandleException:
    def test_sets_response_status_500(self, pyramid_request):
        handle_exception(pyramid_request, Mock())

        assert pyramid_request.response.status_int == 500


@pytest.mark.usefixtures("view_config")
class TestJsonView:
    # pylint: disable=unsubscriptable-object
    def test_sets_accept(self):
        result = json_view()

        assert result["accept"] == "application/json"

    def test_sets_renderer(self):
        result = json_view()

        assert result["renderer"] == "json"

    def test_passes_through_other_kwargs(self):
        result = json_view(foo="bar", baz="qux")

        assert result["foo"] == "bar"
        assert result["baz"] == "qux"

    def test_allows_overriding_accept(self):
        result = json_view(accept="application/ld+json")

        assert result["accept"] == "application/ld+json"

    def test_allows_overriding_renderer(self):
        result = json_view(renderer="h:some/template.json.jinja2")

        assert result["renderer"] == "h:some/template.json.jinja2"

    @pytest.fixture
    def view_config(self, patch):
        def _return_kwargs(**kwargs):
            return kwargs

        view_config = patch("h.util.view.view_config")
        view_config.side_effect = _return_kwargs
        return view_config
