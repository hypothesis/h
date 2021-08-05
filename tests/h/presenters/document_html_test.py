from unittest import mock

import jinja2
import pytest

from h.presenters.document_html import DocumentHTMLPresenter


class TestDocumentHTMLPresenter:
    def test_filename_with_http_uri(self):
        presenter = self.presenter(
            document_uris=[mock.Mock(uri="http://example.com/example.html")]
        )

        assert not presenter.filename

    def test_filename_with_file_uri(self):
        presenter = self.presenter(
            document_uris=[mock.Mock(uri="file:///home/seanh/MyFile.pdf")]
        )

        assert presenter.filename == "MyFile.pdf"

    def test_filename_returns_Markup(self):
        presenter = self.presenter(
            document_uris=[mock.Mock(uri="file:///home/seanh/MyFile.pdf")]
        )

        assert isinstance(presenter.filename, jinja2.Markup)

    def test_filename_with_FILE_uri(self):
        presenter = self.presenter(
            document_uris=[mock.Mock(uri="FILE:///home/seanh/MyFile.pdf")]
        )

        assert presenter.filename == "MyFile.pdf"

    def test_filename_with_folder(self):
        presenter = self.presenter(
            document_uris=[mock.Mock(uri="file:///home/seanh/My%20Documents/")]
        )

        assert not presenter.filename

    def test_filename_with_no_uri(self):
        # self.uri should always be unicode, the worst it should ever be is an
        # empty string.
        presenter = self.presenter(document_uris=[mock.Mock(uri="")])

        assert not presenter.filename

    def test_filename_with_nonsense_uri(self):
        presenter = self.presenter(document_uris=[mock.Mock(uri="foobar")])

        assert not presenter.filename

    def test_href_returns_web_uri_if_document_has_one(self):
        web_uri = "http://www.example.com/example.html"

        assert self.presenter(web_uri=web_uri).href == web_uri

    def test_href_returns_empty_string_for_document_with_no_web_uri(self):
        assert not self.presenter(web_uri=None).href

    def test_href_returns_Markup(self):
        web_uri = "http://www.example.com/example.html"

        assert isinstance(self.presenter(web_uri=web_uri).href, jinja2.Markup)

    link_text_fixtures = pytest.mark.usefixtures("title")

    @link_text_fixtures
    def test_link_text_with_non_http_title(self, title):
        """If .title doesn't start with http(s) it should just use it."""
        title.return_value = "Example Document"

        assert self.presenter().link_text == "Example Document"

    @link_text_fixtures
    def test_link_text_with_http_title(self, title):
        """
        If .title is an http URI .link_test should use it.

        This happens when an annotation's document has no title, so .title
        falls back on the URI instead.

        """
        title.return_value = "http://www.example.com/example.html"

        assert self.presenter().link_text == "www.example.com/example.html"

    @link_text_fixtures
    def test_link_text_with_https_title(self, title):
        """
        If .title is an https URI .link_test should use it.

        This happens when an annotation's document has no title, so .title
        falls back on the URI instead.

        """
        title.return_value = "https://www.example.com/example.html"

        assert self.presenter().link_text == "www.example.com/example.html"

    @link_text_fixtures
    def test_link_text_returns_Markup_if_title_returns_Markup(self, title):
        for title_ in (
            jinja2.Markup("Example Document"),
            jinja2.Markup("http://www.example.com/example.html"),
            jinja2.Markup("https://www.example.com/example.html"),
        ):
            title.return_value = title_
            assert isinstance(self.presenter().link_text, jinja2.Markup)

    hostname_or_filename_fixtures = pytest.mark.usefixtures("uri", "filename")

    @hostname_or_filename_fixtures
    def test_hostname_or_filename_returns_filename_for_files(self, filename):
        filename.return_value = "MyFile.pdf"

        assert self.presenter().hostname_or_filename == "MyFile.pdf"

    @hostname_or_filename_fixtures
    def test_hostname_or_filename_returns_Markup_if_filename_does(self, filename):
        filename.return_value = jinja2.Markup("MyFile.pdf")

        assert isinstance(self.presenter().hostname_or_filename, jinja2.Markup)

    @hostname_or_filename_fixtures
    def test_hostname_or_filename_unquotes_filenames(self, filename):
        filename.return_value = "My%20File.pdf"

        assert self.presenter().hostname_or_filename == "My File.pdf"

    @hostname_or_filename_fixtures
    def test_hostname_or_filename_returns_hostname_for_non_files(self, uri, filename):
        filename.return_value = ""
        uri.return_value = "http://www.example.com/example.html"

        assert self.presenter().hostname_or_filename == "www.example.com"

    @hostname_or_filename_fixtures
    def test_hostname_or_filename_returns_Markup_when_uri_does(self, uri, filename):
        filename.return_value = ""
        uri.return_value = jinja2.Markup("http://www.example.com/example.html")

        assert isinstance(self.presenter().hostname_or_filename, jinja2.Markup)

    @hostname_or_filename_fixtures
    def test_hostname_or_filename_with_empty_string_for_uri(self, uri, filename):
        filename.return_value = ""
        uri.return_value = ""

        assert isinstance(self.presenter().hostname_or_filename, str)

    @hostname_or_filename_fixtures
    def test_hostname_or_filename_with_nonsense_uri(self, uri, filename):
        filename.return_value = ""

        # urlparse.urlparse(u"foobar").hostname is None, make sure this doesn't
        # trip up .hostname_or_filename.
        uri.return_value = "foobar"

        assert isinstance(self.presenter().hostname_or_filename, str)

    title_fixtures = pytest.mark.usefixtures("uri", "filename")

    @title_fixtures
    def test_title_with_a_document_that_has_a_title(self):
        """If the document has a title it should use it."""
        title = "document title"

        assert self.presenter(title=title).title == title

    @title_fixtures
    def test_title_escapes_html_in_document_titles(self):
        spam_link = '<a href="http://example.com/rubies">Buy rubies!!!</a>'

        title = self.presenter(title=spam_link).title

        assert jinja2.escape(spam_link) in title
        for char in ["<", ">", '"', "'"]:
            assert char not in title
        assert isinstance(title, jinja2.Markup)

    @title_fixtures
    def test_title_with_file_uri(self, filename):
        # If the document has no title and the annotation has a file:// uri
        # then it should return the filename part only."""
        filename.return_value = "MyFile.pdf"

        assert self.presenter(title=None).title == "MyFile.pdf"

    @title_fixtures
    def test_title_returns_Markup_when_filename_returns_Markup(self, filename):
        filename.return_value = jinja2.Markup("MyFile.pdf")

        assert isinstance(self.presenter(title=None).title, jinja2.Markup)

    @title_fixtures
    def test_title_unquotes_uris(self, uri, filename):
        filename.return_value = ""  # This is not a file:// URI.
        uri.return_value = "http://example.com/example%201.html"

        assert self.presenter(title=None).title == ("http://example.com/example 1.html")

    @title_fixtures
    def test_title_returns_Markup_when_uri_returns_Markup(self, uri, filename):
        filename.return_value = ""  # This is not a file:// URI.
        uri.return_value = jinja2.Markup("http://example.com/example.html")

        assert isinstance(self.presenter(title=None).title, jinja2.Markup)

    @title_fixtures
    def test_title_when_document_has_None_for_title(self, uri, filename):
        """If title is None for its title it should use the uri instead."""
        uri.return_value = "http://example.com/example.html"
        filename.return_value = ""  # This is not a file:// URI.

        assert self.presenter(title=None).title == ("http://example.com/example.html")

    @title_fixtures
    @pytest.mark.parametrize("title", [23, 23.7, False, {"foo": "bar"}, [1, 2, 3]])
    def test_title_when_document_title_is_not_a_string(self, uri, filename, title):
        """If title is None it should use the uri instead."""
        uri.return_value = "http://example.com/example.html"
        filename.return_value = ""  # This is not a file:// URI.

        assert isinstance(self.presenter(title=title).title, str)

    @title_fixtures
    def test_title_when_document_has_empty_string_for_title(self, uri, filename):
        """If title is "" it should use the uri instead."""
        uri.return_value = "http://example.com/example.html"
        filename.return_value = ""  # This is not a file:// URI.

        assert self.presenter(title="").title == ("http://example.com/example.html")

    @title_fixtures
    def test_title_when_no_document_title_no_filename_and_no_uri(self, uri, filename):
        uri.return_value = ""
        filename.return_value = ""

        assert not self.presenter(title=None).title

    def test_web_uri_returns_document_web_uri(self):
        """
        It just returns Document.web_uri for non-via web_uris.

        If Document.web_uri is a string that doesn't start with
        https://via.hypothes.is/ then DocumentHTMLPresenter.web_uri should
        just return Document.web_uri.

        """
        non_via_uri = "http://example.com/page"

        assert self.presenter(web_uri=non_via_uri).web_uri == non_via_uri

    def test_web_uri_returns_None_if_document_web_uri_is_None(self):
        assert self.presenter(web_uri=None).web_uri is None

    @pytest.mark.parametrize(
        "via_url", ("https://via.hypothes.is", "https://via.hypothes.is/")
    )
    def test_web_uri_returns_via_front_page(self, via_url):
        """It doesn't strip https://via.hypothes.is if that's the entire URL."""
        assert self.presenter(web_uri=via_url).web_uri == via_url

    def test_web_uri_does_not_strip_http_via(self):
        """
        It doesn't strip non-SSL http://via.hypothes.is.

        Since http://via.hypothes.is redirects to https://via.hypothes.is
        anyway, and we don't currently have any http://via.hypothes.is
        URIs in our production DB, DocumentHTMLPresenter.web_uri only strips
        https://via.hypothes.is/ and ignores http://via.hypothes.is/.
        """
        uri = "http://via.hypothes.is/http://example.com/page"

        assert self.presenter(web_uri=uri).web_uri == uri

    @pytest.mark.parametrize("path", ("foo", "http://example.com"))
    def test_web_uri_strips_via(self, path):
        """
        It strips any https://via.hypothes.is/ prefix from Document.web_uri.

        If Document.web_uri is https://via.hypothes.is/<path>, for any <path>
        (whether path is a URL or not), DocumentHTMLPresenter.web_uri just
        returns <path> with the https://via.hypothes.is/ prefix removed.

        """
        uri = "https://via.hypothes.is/" + path

        assert self.presenter(web_uri=uri).web_uri == path

    def presenter(self, **kwargs):
        return DocumentHTMLPresenter(mock.Mock(**kwargs))

    @pytest.fixture
    def filename(self, patch):
        return patch(
            "h.presenters.document_html.DocumentHTMLPresenter.filename",
            autospec=None,
            new_callable=mock.PropertyMock,
        )

    @pytest.fixture
    def title(self, patch):
        return patch(
            "h.presenters.document_html.DocumentHTMLPresenter.title",
            autospec=None,
            new_callable=mock.PropertyMock,
        )

    @pytest.fixture
    def uri(self, patch):
        return patch(
            "h.presenters.document_html.DocumentHTMLPresenter.uri",
            autospec=None,
            new_callable=mock.PropertyMock,
        )
