from unittest.mock import Mock

import pytest

from h.util.view import handle_exception, json_view


@pytest.mark.usefixtures("sys_exc_info")
class TestHandleException:
    def test_sets_response_status_500(self, pyramid_request):
        handle_exception(pyramid_request, Mock())

        assert pyramid_request.response.status_int == 500

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        return pyramid_request

    @pytest.fixture
    def latest_exception(self):
        return Exception("Last exception raised in thread")

    @pytest.fixture
    def sys_exc_info(self, patch, latest_exception):
        sys_exc_info = patch("h.util.view._exc_info")
        sys_exc_info.return_value = (type(latest_exception), latest_exception, None)
        return sys_exc_info


@pytest.mark.usefixtures("view_config")
class TestJsonView:
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
