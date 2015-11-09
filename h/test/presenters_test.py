import pytest
import mock
import jinja2

from h import presenters


def _annotation(annotation=None, **kwargs):
    """Return an AnnotationHTMLPresenter for the given annotation.

    If no annotation is given a mock will be used, and any keyword arguments
    will be forwarded to the mock.Mock() constructor.

    """
    return presenters.AnnotationHTMLPresenter(
        annotation or mock.Mock(**kwargs))


def test_uri_is_escaped():
    spam_link = '<a href="http://example.com/rubies">Buy rubies!!!</a>'

    uri = _annotation(uri='http://</a>' + spam_link).uri

    assert jinja2.escape(spam_link) in uri
    for char in ['<', '>', '"', "'"]:
        assert char not in uri


def test_uri_returns_Markup():
    assert isinstance(_annotation(uri="http://foo.com").uri, jinja2.Markup)


def test_filename_with_http_uri():
    assert _annotation(uri="http://example.com/example.html").filename == ""


def test_filename_with_file_uri():
    assert _annotation(uri="file:///home/seanh/MyFile.pdf").filename == (
        "MyFile.pdf")


def test_filename_returns_Markup():
    annotation = _annotation(
        uri=jinja2.Markup("file:///home/seanh/MyFile.pdf"))
    assert isinstance(annotation.filename, jinja2.Markup)


def test_filename_with_FILE_uri():
    assert _annotation(uri="FILE:///home/seanh/MyFile.pdf").filename == (
        "MyFile.pdf")


def test_filename_with_folder():
    assert _annotation(uri="file:///home/seanh/My%20Documents/").filename == ""


def test_filename_with_no_uri():
    # self.uri should always be unicode, the worst is should ever be is an
    # empty string.
    assert _annotation(uri=u"").filename == ""


def test_filename_with_nonsense_uri():
    assert _annotation(uri=u"foobar").filename == ""


title_fixtures = pytest.mark.usefixtures('uri', 'filename')


@title_fixtures
def test_title_with_a_document_that_has_a_title():
    """If the document has a title it should use it."""
    annotation = _annotation(document={'title': 'document title'})
    assert annotation.title == 'document title'


@title_fixtures
def test_title_escapes_html_in_document_titles():
    spam_link = '<a href="http://example.com/rubies">Buy rubies!!!</a>'
    annotation = _annotation(document={'title': '</a>' + spam_link})

    title = annotation.title

    assert jinja2.escape(spam_link) in title
    for char in ['<', '>', '"', "'"]:
        assert char not in title
    assert isinstance(title, jinja2.Markup)


@title_fixtures
def test_title_with_file_uri(filename):
    """If the document has no title and the annotation has a file:// uri then
    it should return the filename part only."""
    filename.return_value = "MyFile.pdf"
    annotation = _annotation(document={})

    assert annotation.title == "MyFile.pdf"


@title_fixtures
def test_title_returns_Markup_when_filename_returns_Markup(filename):
    filename.return_value = jinja2.Markup("MyFile.pdf")
    annotation = _annotation(document={})

    assert isinstance(annotation.title, jinja2.Markup)


@title_fixtures
def test_title_unquotes_uris(uri, filename):
    filename.return_value = ""  # This is not a file:// URI.
    uri.return_value = "http://example.com/example%201.html"
    annotation = _annotation()

    assert annotation.title == "http://example.com/example 1.html"


@title_fixtures
def test_title_returns_Markup_when_uri_returns_Markup(uri, filename):
    filename.return_value = ""  # This is not a file:// URI.
    uri.return_value = jinja2.Markup("http://example.com/example.html")
    annotation = _annotation()

    assert isinstance(annotation.title, jinja2.Markup)


@title_fixtures
def test_title_when_document_has_None_for_title(uri, filename):
    """If the document has None for its title it should use the uri instead."""
    uri.return_value = "http://example.com/example.html"
    filename.return_value = ""  # This is not a file:// URI.
    annotation = _annotation(document={'title': None})

    assert annotation.title == "http://example.com/example.html"


@title_fixtures
def test_title_when_document_title_is_not_a_string(uri, filename):
    """If the document has None for its title it should use the uri instead."""
    uri.return_value = u"http://example.com/example.html"
    filename.return_value = ""  # This is not a file:// URI.

    for title in (23, 23.7, False, {"foo": "bar"}, [1, 2, 3]):
        annotation = _annotation(document={'title': title})
        assert isinstance(annotation.title, unicode)


@title_fixtures
def test_title_when_document_has_empty_string_for_title(uri, filename):
    """If the document has "" for its title it should use the uri instead."""
    uri.return_value = "http://example.com/example.html"
    filename.return_value = ""  # This is not a file:// URI.
    annotation = _annotation(document={'title': ""})

    assert annotation.title == "http://example.com/example.html"


@title_fixtures
def test_title_when_no_document_title_no_filename_and_no_uri(uri, filename):
    uri.return_value = ""
    filename.return_value = ""
    annotation = _annotation(document={})

    assert annotation.title == ""


@title_fixtures
def test_title_when_annotations_document_is_not_a_dict(uri, filename):
    uri.return_value = "http://www.example.com/example.html"
    filename.return_value = ""  # This is not a file:// URI.

    for document in (False, 23, 12.7, None, [], [1, 2, 3], "foo", u"bar"):
        annotation = _annotation(document=document)
        assert annotation.title == uri.return_value


hostname_or_filename_fixtures = pytest.mark.usefixtures('uri', 'filename')


@hostname_or_filename_fixtures
def test_hostname_or_filename_returns_filename_for_files(filename):
    filename.return_value = "MyFile.pdf"
    annotation = _annotation()

    assert annotation.hostname_or_filename == "MyFile.pdf"


@hostname_or_filename_fixtures
def test_hostname_or_filename_returns_Markup_if_filename_does(filename):
    filename.return_value = jinja2.Markup("MyFile.pdf")
    annotation = _annotation()

    assert isinstance(annotation.hostname_or_filename, jinja2.Markup)


@hostname_or_filename_fixtures
def test_hostname_or_filename_returns_hostname_for_non_files(uri, filename):
    filename.return_value = ""
    uri.return_value = "http://www.example.com/example.html"
    annotation = _annotation()

    assert annotation.hostname_or_filename == "www.example.com"


@hostname_or_filename_fixtures
def test_hostname_or_filename_returns_Markup_when_uri_does(uri, filename):
    filename.return_value = ""
    uri.return_value = jinja2.Markup("http://www.example.com/example.html")
    annotation = _annotation()

    assert isinstance(annotation.hostname_or_filename, jinja2.Markup)


@hostname_or_filename_fixtures
def test_hostname_or_filename_with_empty_string_for_uri(uri, filename):
    filename.return_value = ""
    uri.return_value = u""
    annotation = _annotation()

    assert isinstance(annotation.hostname_or_filename, unicode)


@hostname_or_filename_fixtures
def test_hostname_or_filename_with_nonsense_uri(uri, filename):
    filename.return_value = ""

    # urlparse.urlparse(u"foobar").hostname is None, make sure this doesn't
    # trip up .hostname_or_filename.
    uri.return_value = u"foobar"

    annotation = _annotation()

    assert isinstance(annotation.hostname_or_filename, unicode)


href_fixtures = pytest.mark.usefixtures('uri')


@href_fixtures
def test_href_returns_uri_for_http_uri(uri):
    uri.return_value = "http://www.example.com/example.html"
    assert _annotation().href == uri.return_value


@href_fixtures
def test_href_returns_uri_for_https_uri(uri):
    uri.return_value = "https://www.example.com/example.html"
    assert _annotation().href == uri.return_value


@href_fixtures
def test_href_scheme_matching_is_case_insensitive(uri):
    for uri_ in (
            "HTTP://www.example.com/example.html",
            "HTTPS://www.example.com/example.html"):
        uri.return_value = uri_
        assert _annotation().href == uri_


@href_fixtures
def test_href_returns_empty_string_for_non_http_uris(uri):
    uri.return_value = "file:///MyFile.pdf"
    assert _annotation(uri=uri).href == ""


@href_fixtures
def test_href_returns_Markup_if_uri_returns_Markup(uri):
    uri.return_value = jinja2.Markup("http://www.example.com/example.html")
    assert isinstance(_annotation().href, jinja2.Markup)


link_text_fixtures = pytest.mark.usefixtures('title')


@link_text_fixtures
def test_link_text_with_non_http_title(title):
    """If .title doesn't start with http(s) link_text should just use it."""
    title.return_value = "Example Document"
    assert _annotation().link_text == "Example Document"


@link_text_fixtures
def test_link_text_with_http_title(title):
    """If .title is an http URI .link_test should use it.

    This happens when an annotation's document has no title, so .title falls
    back on the URI instead.

    """
    title.return_value = "http://www.example.com/example.html"
    assert _annotation().link_text == "www.example.com/example.html"


@link_text_fixtures
def test_link_text_with_https_title(title):
    """If .title is an https URI .link_test should use it.

    This happens when an annotation's document has no title, so .title falls
    back on the URI instead.

    """
    title.return_value = "https://www.example.com/example.html"
    assert _annotation().link_text == "www.example.com/example.html"


@link_text_fixtures
def test_link_text_returns_Markup_if_title_returns_Markup(title):
    for title_ in (
            jinja2.Markup("Example Document"),
            jinja2.Markup("http://www.example.com/example.html"),
            jinja2.Markup("https://www.example.com/example.html")):
        title.return_value = title_
        assert isinstance(_annotation().link_text, jinja2.Markup)


document_link_fixtures = pytest.mark.usefixtures(
    'link_text', 'title', 'href', 'hostname_or_filename')


@document_link_fixtures
def test_document_link_happy_path(hostname_or_filename, href, title,
                                  link_text):
    hostname_or_filename.return_value = "www.example.com"
    href.return_value = "http://www.example.com/example.html"
    title.return_value = "Example Document"
    link_text.return_value = "Example Document"

    assert _annotation().document_link == (
        '<a href="http://www.example.com/example.html" '
        'title="Example Document">Example Document</a><br>(www.example.com)')


@document_link_fixtures
def test_document_link_returns_Markup(hostname_or_filename, href, title,
                                      link_text):
    hostname_or_filename.return_value = "www.example.com"
    href.return_value = "http://www.example.com/example.html"
    title.return_value = "Example Document"
    link_text.return_value = "Example Document"

    assert isinstance(_annotation().document_link, jinja2.Markup)


@document_link_fixtures
def test_document_link_hostname_same_as_link_text(hostname_or_filename, href,
                                                  title, link_text):
    """If '(hostname)' is the same as the link text it shouldn't be shown."""
    href.return_value = "http://www.example.com"
    title.return_value = "www.example.com"

    # .hostname_or_filename and .link_text are the same.
    hostname_or_filename.return_value = "www.example.com"
    link_text.return_value = "www.example.com"

    assert _annotation().document_link == (
        '<a href="http://www.example.com" title="www.example.com">'
        'www.example.com</a>')


@document_link_fixtures
def test_document_link_hostname_part_of_link_text(hostname_or_filename, href,
                                                  title, link_text):
    """If '(hostname)' is part of the link text it shouldn't be shown."""
    href.return_value = "http://www.example.com/example.html"
    title.return_value = "www.example.com/example.html"

    # .hostname_or_filename is a substring of .link_text.
    link_text.return_value = "www.example.com/example.html"
    hostname_or_filename.return_value = "www.example.com"

    assert _annotation().document_link == (
        '<a href="http://www.example.com/example.html" '
        'title="www.example.com/example.html">'
        'www.example.com/example.html</a>')


@document_link_fixtures
def test_document_link_truncates_hostname(hostname_or_filename, href, title,
                                          link_text):
    href.return_value = "http://www.example.com/example.html"
    title.return_value = "www.example.com/example.html"
    link_text.return_value = "www.example.com/example.html"

    # .hostname_or_filename is too long.
    hostname_or_filename.return_value = "a" * 70

    expected_hostname = "a" * 60 + "&hellip;"
    expected_result = (
        '<a href="http://www.example.com/example.html" '
        'title="www.example.com/example.html">'
        'www.example.com/example.html</a><br>({hostname})'.format(
            hostname=expected_hostname))
    assert _annotation().document_link == expected_result


@document_link_fixtures
def test_document_link_truncates_link_text(hostname_or_filename, href, title,
                                           link_text):
    hostname_or_filename.return_value = "www.example.com"
    href.return_value = "http://www.example.com/example.html"
    title.return_value = "www.example.com/example.html"

    # .link_text is too long.
    link_text.return_value = "a" * 70

    expected_link_text = "a" * 60 + "&hellip;"
    expected_result = (
        '<a href="http://www.example.com/example.html" '
        'title="www.example.com/example.html">{link_text}</a><br>'
        '(www.example.com)'.format(link_text=expected_link_text))
    assert _annotation().document_link == expected_result


@document_link_fixtures
def test_document_link_hostname_but_no_href(hostname_or_filename, href, title,
                                            link_text):
    hostname_or_filename.return_value = "www.example.com"
    title.return_value = "Example Document"
    link_text.return_value = "Example Document"

    # No .href.
    href.return_value = ""

    assert _annotation().document_link == (
        '<a title="Example Document">Example Document</a><br>'
        '(www.example.com)')


@document_link_fixtures
def test_document_link_href_but_no_hostname(hostname_or_filename, href, title,
                                            link_text):
    href.return_value = "http://www.example.com/example.html"
    title.return_value = "www.example.com/example.html"
    link_text.return_value = "www.example.com/example.html"

    # No .hostname_or_filename.
    hostname_or_filename.return_value = ""

    assert _annotation().document_link == (
        '<a href="http://www.example.com/example.html" '
        'title="www.example.com/example.html">'
        'www.example.com/example.html</a>')


@document_link_fixtures
def test_document_link_no_href_and_no_hostname(hostname_or_filename, href,
                                               title, link_text):
    title.return_value = "www.example.com/example.html"
    link_text.return_value = "www.example.com/example.html"

    # No .href and no .hostname_or_filename.
    href.return_value = ""
    hostname_or_filename.return_value = ""

    assert _annotation().document_link == (
        '<a title="www.example.com/example.html">'
        'www.example.com/example.html</a>')


def test_description():
    annotation = _annotation(
        annotation={
            "target": [{'selector': [{'exact': 'selected text'}]}],
            "text": "entered text"
        }
    )

    assert annotation.description == (
        "&lt;blockquote&gt;selected text&lt;/blockquote&gt;entered text")


def test_created_day_string_from_annotation():
    annotation = _annotation(
        annotation={"created": "2015-09-04T17:37:49.517852+00:00"})
    assert annotation.created_day_string == '2015-09-04'


@pytest.fixture
def uri(request):
    patcher = mock.patch(
        'h.presenters.AnnotationHTMLPresenter.uri',
        new_callable=mock.PropertyMock)
    result = patcher.start()
    request.addfinalizer(patcher.stop)
    return result


@pytest.fixture
def filename(request):
    patcher = mock.patch(
        'h.presenters.AnnotationHTMLPresenter.filename',
        new_callable=mock.PropertyMock)
    result = patcher.start()
    request.addfinalizer(patcher.stop)
    return result


@pytest.fixture
def title(request):
    patcher = mock.patch(
        'h.presenters.AnnotationHTMLPresenter.title',
        new_callable=mock.PropertyMock)
    result = patcher.start()
    request.addfinalizer(patcher.stop)
    return result


@pytest.fixture
def link_text(request):
    patcher = mock.patch(
        'h.presenters.AnnotationHTMLPresenter.link_text',
        new_callable=mock.PropertyMock)
    result = patcher.start()
    request.addfinalizer(patcher.stop)
    return result


@pytest.fixture
def href(request):
    patcher = mock.patch(
        'h.presenters.AnnotationHTMLPresenter.href',
        new_callable=mock.PropertyMock)
    result = patcher.start()
    request.addfinalizer(patcher.stop)
    return result


@pytest.fixture
def hostname_or_filename(request):
    patcher = mock.patch(
        'h.presenters.AnnotationHTMLPresenter.hostname_or_filename',
        new_callable=mock.PropertyMock)
    result = patcher.start()
    request.addfinalizer(patcher.stop)
    return result
