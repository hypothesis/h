# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime

import pytest
import mock
import jinja2

from h.presenters.annotation_html import AnnotationHTMLPresenter


class TestAnnotationHTMLPresenter(object):
    def _annotation(self, annotation=None, **kwargs):
        """Return an AnnotationHTMLPresenter for the given annotation.

        If no annotation is given a mock will be used, and any keyword
        arguments will be forwarded to the mock.Mock() constructor.

        """
        return AnnotationHTMLPresenter(annotation or mock.Mock(**kwargs))

    def test_uri_is_escaped(self):
        spam_link = '<a href="http://example.com/rubies">Buy rubies!!!</a>'

        uri = self._annotation(target_uri="http://</a>" + spam_link).uri

        assert jinja2.escape(spam_link) in uri
        for char in ["<", ">", '"', "'"]:
            assert char not in uri

    def test_uri_returns_Markup(self):
        assert isinstance(
            self._annotation(target_uri="http://foo.com").uri, jinja2.Markup
        )

    def test_quote(self):
        annotation = self._annotation(
            annotation=mock.Mock(
                target_selectors=[{"exact": "selected text"}], text="entered text"
            )
        )

        assert annotation.quote == ("selected text")

    def test_username(self):
        annotation = self._annotation(
            annotation=mock.Mock(userid="acct:jdoe@hypothes.is")
        )

        assert annotation.username == ("jdoe")

    def test_shared(self):
        annotation = self._annotation(annotation=mock.Mock())

        assert annotation.shared == annotation.annotation.shared

    def test_tags(self):
        annotation = self._annotation(annotation=mock.Mock())

        assert annotation.tags == annotation.annotation.tags

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, jinja2.Markup("")),
            ("", jinja2.Markup("")),
            ("donkeys with umbrellas", jinja2.Markup("donkeys with umbrellas")),
        ],
    )
    def test_text_rendered(self, value, expected):
        annotation = self._annotation(annotation=mock.Mock(text_rendered=value))

        assert annotation.text_rendered == expected

    def test_description(self):
        annotation = self._annotation(
            annotation=mock.Mock(
                target_selectors=[{"exact": "selected text"}], text="entered text"
            )
        )

        assert annotation.description == (
            "&lt;blockquote&gt;selected text&lt;/blockquote&gt;entered text"
        )

    def test_created_day_string_from_annotation(self):
        annotation = self._annotation(
            annotation=mock.Mock(
                created=datetime.datetime(2015, 9, 4, 17, 37, 49, 517852)
            )
        )
        assert annotation.created_day_string == "2015-09-04"

    def test_it_does_not_crash_when_annotation_has_no_document(self):
        annotation = mock.Mock(document=None)
        presenter = AnnotationHTMLPresenter(annotation)

        # Some AnnotationHTMLPresenter properties rely on the annotation's
        # document. Call them all to make sure that none of them crash when
        # the document is None.
        # pylint: disable=pointless-statement
        presenter.document_link
        presenter.hostname_or_filename
        presenter.href
        presenter.link_text
        presenter.title

    @mock.patch("h.presenters.annotation_html.DocumentHTMLPresenter")
    def test_it_does_not_init_DocumentHTMLPresenter_if_no_document(
        self, DocumentHTMLPresenter
    ):
        """
        It shouldn't init DocumentHTMLPresenter if document is None.

        We don't want DocumentHTMLPresenter to be initialized with None for
        a document, so make sure that AnnotationHTMLPresenter doesn't do so.

        """
        annotation = mock.Mock(document=None)
        presenter = AnnotationHTMLPresenter(annotation)

        # Call all these as well to make sure that none of them cause a
        # DocumentHTMLPresenter to be initialized.
        # pylint: disable=pointless-statement
        presenter.document_link
        presenter.hostname_or_filename
        presenter.href
        presenter.link_text
        presenter.title

        assert not DocumentHTMLPresenter.called
