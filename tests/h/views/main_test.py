import pytest
from h_matchers import All, Any
from pyramid import httpexceptions

from h.models import Annotation
from h.traversal import AnnotationContext
from h.views import main


def _fake_sidebar_app(request, extra):  # pylint:disable=unused-argument
    return extra


@pytest.mark.usefixtures("routes")
def test_og_document(factories, pyramid_request, sidebar_app):
    annotation = factories.Annotation(userid="acct:foo@example.com")
    context = AnnotationContext(annotation)
    sidebar_app.side_effect = _fake_sidebar_app

    ctx = main.annotation_page(context, pyramid_request)

    expected = Any.dict.containing(
        {
            "content": All.of(
                [
                    Any.string.containing("foo@example.com"),
                    Any.string.containing(annotation.document.title),
                ]
            )
        }
    )

    assert expected in ctx["meta_attrs"]


@pytest.mark.usefixtures("routes")
def test_og_no_document(pyramid_request, sidebar_app):
    annotation = Annotation(id="123", userid="foo", target_uri="http://example.com")
    context = AnnotationContext(annotation)
    sidebar_app.side_effect = _fake_sidebar_app

    ctx = main.annotation_page(context, pyramid_request)

    expected = Any.dict.containing({"content": Any.string.containing("foo")})

    assert expected in ctx["meta_attrs"]


@pytest.mark.usefixtures("sidebar_app", "routes")
class TestStreamUserRedirect:
    def test_it_redirects_to_activity_page_with_tags(self, pyramid_request):
        pyramid_request.params["q"] = "tag:foo"
        pyramid_request.matchdict["tag"] = "foo"
        with pytest.raises(httpexceptions.HTTPFound) as exc:
            main.stream(None, pyramid_request)

        assert exc.value.location == "http://example.com/search?q=tag%3Afoo"

    def test_it_redirects_to_activity_page_with_tags_containing_spaces(
        self, pyramid_request
    ):
        pyramid_request.params["q"] = "tag:foo bar"
        pyramid_request.matchdict["tag"] = "foo bar"
        with pytest.raises(httpexceptions.HTTPFound) as exc:
            main.stream(None, pyramid_request)

        assert exc.value.location == "http://example.com/search?q=tag%3A%22foo+bar%22"

    def test_it_redirects_to_activity_page_if_q_length_great_than_2(
        self, pyramid_request
    ):
        pyramid_request.params["q"] = "tag:foo:bar"
        pyramid_request.matchdict["tag"] = "foo:bar"
        with pytest.raises(httpexceptions.HTTPFound) as exc:
            main.stream(None, pyramid_request)

        assert exc.value.location == "http://example.com/search?q=tag%3Afoo%3Abar"

    def test_it_does_not_redirect_to_activity_page_if_no_q_param(
        self, sidebar_app, pyramid_request
    ):
        pyramid_request.matchdict["tag"] = "foo"

        main.stream(None, pyramid_request)

        assert sidebar_app.called

    def test_it_does_not_redirect_to_activity_page_if_no_tag_key(
        self, sidebar_app, pyramid_request
    ):
        pyramid_request.params["q"] = "foo"

        main.stream(None, pyramid_request)

        assert sidebar_app.called

    def test_it_does_not_redirect_to_activity_page_if_no_tag_key_value(
        self, sidebar_app, pyramid_request
    ):
        pyramid_request.params["q"] = "tag-foo"

        main.stream(None, pyramid_request)

        assert sidebar_app.called

    def test_it_redirects_to_user_activity_page(self, pyramid_request):
        pyramid_request.matchdict["user"] = "bob"

        with pytest.raises(httpexceptions.HTTPFound) as exc:
            main.stream_user_redirect(pyramid_request)

        assert exc.value.location == "http://example.com/user/bob"

    def test_it_extracts_username_from_account_id(self, pyramid_request):
        pyramid_request.matchdict["user"] = "acct:bob@hypothes.is"

        with pytest.raises(httpexceptions.HTTPFound) as exc:
            main.stream_user_redirect(pyramid_request)

        assert exc.value.location == "http://example.com/user/bob"

    def test_doesnt_choke_on_invalid_userids(self, pyramid_request):
        pyramid_request.matchdict["user"] = "acct:bob"

        with pytest.raises(httpexceptions.HTTPFound) as exc:
            main.stream_user_redirect(pyramid_request)

        assert exc.value.location == "http://example.com/user/acct:bob"

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("activity.search", "/search")
        pyramid_config.add_route("activity.user_search", "/user/{username}")
        pyramid_config.add_route("stream", "/stream")
        pyramid_config.add_route("stream_atom", "/stream.atom")
        pyramid_config.add_route("stream_rss", "/stream.rss")


@pytest.fixture
def sidebar_app(patch):
    return patch("h.views.main.sidebar_app")


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("api.annotation", "/api/ann/{id}")
    pyramid_config.add_route("api.index", "/api/index")
    pyramid_config.add_route("index", "/index")
