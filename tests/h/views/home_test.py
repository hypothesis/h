from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound

from h.views.home import index_redirect, via_redirect


@pytest.mark.usefixtures("routes")
class TestIndexRedirect:
    def test_redirects_to_user_search_page_for_user(self, factories, pyramid_request):
        pyramid_request.user = factories.User(username="petronela")

        with pytest.raises(HTTPFound) as exc:
            index_redirect(None, pyramid_request)

        assert exc.value.location == "http://example.com/u/s/petronela"

    def test_redirects_to_search_if_no_user(self, pyramid_request):
        pyramid_request.user = None

        with pytest.raises(HTTPFound) as exc:
            index_redirect(None, pyramid_request)

        assert exc.value.location == "http://example.com/s"

    def test_respects_setting(self, pyramid_request):
        pyramid_request.registry.settings[
            "h.homepage_redirect_url"
        ] = "https://web.hypothes.is"
        pyramid_request.user = None

        with pytest.raises(HTTPFound) as exc:
            index_redirect(None, pyramid_request)

        assert exc.value.location == "https://web.hypothes.is"


class TestViaRedirect:
    def test_it(self, pyramid_request):
        pyramid_request.params["url"] = "http://example.com"

        with pytest.raises(HTTPFound) as exc:
            via_redirect(sentinel.context, pyramid_request)

        assert exc.value.location == "https://via.hypothes.is/http://example.com"

    def test_it_raises_with_no_url(self, pyramid_request):
        pyramid_request.params["url"] = None

        with pytest.raises(HTTPBadRequest):
            via_redirect(sentinel.context, pyramid_request)


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("activity.search", "/s")
    pyramid_config.add_route("activity.user_search", "/u/s/{username}")
