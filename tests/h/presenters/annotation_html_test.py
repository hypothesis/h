import datetime

import pytest
from jinja2 import Markup

from h.presenters.annotation_html import AnnotationHTMLPresenter


class TestAnnotationHTMLPresenter:
    def test_uri_is_escaped(self, annotation, presenter):
        annotation.target_uri = "http://<markup v='q' v2=\"q2\">"

        uri = presenter.uri

        assert uri == Markup("http://&lt;markup v=&#39;q&#39; v2=&#34;q2&#34;&gt;")

    def test_quote(self, annotation, presenter):
        annotation.target_selectors = [
            {"decoy": 1},
            # We pick the first selector with "exact" and escape it
            {"exact": "<selected text>"},
            {"decoy": 2},
        ]

        assert presenter.quote == Markup("&lt;selected text&gt;")

    def test_quote_with_no_selector(self, annotation, presenter):
        annotation.target_selectors = []

        assert not presenter.quote

    def test_username(self, annotation, presenter):
        annotation.userid = "acct:jdoe@hypothes.is"

        assert presenter.username == "jdoe"

    @pytest.mark.parametrize(
        "method", ("id", "created", "updated", "userid", "shared", "tags")
    )
    def test_annotation_proxies(self, annotation, presenter, method):
        assert getattr(presenter, method) == getattr(annotation, method)

    @pytest.mark.parametrize(
        "method,proxied_method",
        (
            ("document_link", "link"),
            ("filename", "filename"),
            ("hostname_or_filename", "hostname_or_filename"),
            ("href", "href"),
            ("link_text", "link_text"),
            ("title", "title"),
        ),
    )
    def test_document_proxies(self, presenter, method, proxied_method):
        # Note that the "document" here is actually a `DocumentHTMLPresenter`
        assert getattr(presenter, method) == getattr(presenter.document, proxied_method)

        presenter.document = None
        assert not getattr(presenter, method)

    @pytest.mark.parametrize(
        "value,expected",
        [(None, Markup("")), ("", Markup("")), ("text", Markup("text"))],
    )
    def test_text_rendered(self, annotation, presenter, value, expected):
        annotation._text_rendered = value  # pylint:disable=protected-access

        assert presenter.text_rendered == expected

    def test_description(self, annotation, presenter):
        annotation.target_selectors = [{"exact": "TARGET_SELECTOR"}]
        annotation.text = "TEXT"

        assert presenter.description == (
            "&lt;blockquote&gt;TARGET_SELECTOR&lt;/blockquote&gt;TEXT"
        )

    def test_created_day_string_from_annotation(self, annotation, presenter):
        annotation.created = datetime.datetime(2015, 9, 4, 17, 37, 49, 517852)

        assert presenter.created_day_string == "2015-09-04"

    def test_it_does_not_init_DocumentHTMLPresenter_if_no_document(
        self, annotation, DocumentHTMLPresenter
    ):
        annotation.document = None
        presenter = AnnotationHTMLPresenter(annotation)

        # Call all these as well to make sure that none of them cause a
        # DocumentHTMLPresenter to be initialized.
        _ = (
            presenter.document_link,
            presenter.hostname_or_filename,
            presenter.href,
            presenter.link_text,
            presenter.title,
        )

        DocumentHTMLPresenter.assert_not_called()

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()

    @pytest.fixture
    def presenter(self, annotation):
        return AnnotationHTMLPresenter(annotation)

    @pytest.fixture
    def DocumentHTMLPresenter(self, patch):
        return patch("h.presenters.annotation_html.DocumentHTMLPresenter")
