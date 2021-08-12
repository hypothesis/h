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

    def test_username(self, annotation, presenter):
        annotation.userid = "acct:jdoe@hypothes.is"

        assert presenter.username == "jdoe"

    def test_shared(self, annotation, presenter):
        assert presenter.shared == annotation.shared

    def test_tags(self, annotation, presenter):
        assert presenter.tags == annotation.tags

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, Markup("")),
            ("", Markup("")),
            ("donkeys with umbrellas", Markup("donkeys with umbrellas")),
        ],
    )
    def test_text_rendered(self, annotation, presenter, value, expected):
        annotation._text_rendered = value

        assert presenter.text_rendered == expected

    def test_description(self, annotation, presenter):
        annotation.target_selectors = [{"exact": "selected text"}]
        annotation.text = "entered text"

        assert presenter.description == (
            f"&lt;blockquote&gt;selected text&lt;/blockquote&gt;entered text"
        )

    def test_created_day_string_from_annotation(self, annotation, presenter):
        annotation.created = datetime.datetime(2015, 9, 4, 17, 37, 49, 517852)

        assert presenter.created_day_string == "2015-09-04"

    def test_it_does_not_init_DocumentHTMLPresenter_if_no_document(
        self, annotation, presenter, DocumentHTMLPresenter
    ):
        annotation.document = None

        # Call all these as well to make sure that none of them cause a
        # DocumentHTMLPresenter to be initialized.
        _ = presenter.document_link
        _ = presenter.hostname_or_filename
        _ = presenter.href
        _ = presenter.link_text
        _ = presenter.title

        #  We don't want DocumentHTMLPresenter to be initialized with None for
        #  a document, so make sure that AnnotationHTMLPresenter doesn't do so.
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
