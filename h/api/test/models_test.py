# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
import itertools
import re
import urllib

import jinja2
import pytest
from mock import patch
from mock import PropertyMock

from h.api import models

analysis = models.Annotation.__analysis__


def test_strip_scheme_char_filter():
    f = analysis['char_filter']['strip_scheme']
    p = f['pattern']
    r = f['replacement']
    assert(re.sub(p, r, 'http://ping/pong#hash') == 'ping/pong#hash')
    assert(re.sub(p, r, 'chrome-extension://1234/a.js') == '1234/a.js')
    assert(re.sub(p, r, 'a+b.c://1234/a.js') == '1234/a.js')
    assert(re.sub(p, r, 'uri:x-pdf:1234') == 'x-pdf:1234')
    assert(re.sub(p, r, 'example.com') == 'example.com')
    # This is ambiguous, and possibly cannot be expected to work.
    # assert(re.sub(p, r, 'localhost:5000') == 'localhost:5000')


def test_path_url_filter():
    patterns = analysis['filter']['path_url']['patterns']
    assert(captures(patterns, 'example.com/foo/bar?query#hash') == [
        'example.com/foo/bar'
    ])
    assert(captures(patterns, 'example.com/foo/bar/') == [
        'example.com/foo/bar/'
    ])


def test_rstrip_slash_filter():
    p = analysis['filter']['rstrip_slash']['pattern']
    r = analysis['filter']['rstrip_slash']['replacement']
    assert(re.sub(p, r, 'example.com/') == 'example.com')
    assert(re.sub(p, r, 'example.com/foo/bar/') == 'example.com/foo/bar')


def test_uri_part_tokenizer():
    text = 'http://a.b/foo/bar?c=d#stuff'
    pattern = analysis['tokenizer']['uri_part']['pattern']
    assert(re.split(pattern, text) == [
        'http', '', '', 'a', 'b', 'foo', 'bar', 'c', 'd', 'stuff'
    ])

    text = urllib.quote_plus(text)
    assert(re.split(pattern, 'http://jump.to/?u=' + text) == [
        'http', '', '', 'jump', 'to', '', 'u',
        'http', '', '', 'a', 'b', 'foo', 'bar', 'c', 'd', 'stuff'
    ])


def captures(patterns, text):
    return list(itertools.chain(*(groups(p, text) for p in patterns)))


def groups(pattern, text):
    return re.search(pattern, text).groups() or []


def test_uri():
    assert models.Annotation(uri="http://foo.com").uri == "http://foo.com"


def test_uri_with_no_uri():
    assert models.Annotation().uri == ""


def test_uri_is_escaped():
    spam_link = '<a href="http://example.com/rubies">Buy rubies!!!</a>'
    annotation = models.Annotation(uri='http://</a>' + spam_link)

    uri = annotation.uri

    assert jinja2.escape(spam_link) in uri
    for char in ['<', '>', '"', "'"]:
        assert char not in uri


def test_uri_returns_Markup():
    assert isinstance(
        models.Annotation(uri="http://foo.com").uri, jinja2.Markup)


def test_uri_when_uri_is_not_a_string():
    for uri in (True, None, 23, 23.7, {"foo": False}, [1, 2, 3]):
        assert isinstance(models.Annotation(uri=uri).uri, unicode)


@patch("h.api.models.Annotation.uri", new_callable=PropertyMock)
def test_filename_with_http_uri(uri):
    uri.return_value = "http://example.com/example.html"

    assert models.Annotation().filename == ""


@patch("h.api.models.Annotation.uri", new_callable=PropertyMock)
def test_filename_with_file_uri(uri):
    uri.return_value = "file:///home/seanh/MyFile.pdf"

    assert models.Annotation().filename == "MyFile.pdf"


@patch("h.api.models.Annotation.uri", new_callable=PropertyMock)
def test_filename_returns_Markup(uri):
    uri.return_value = jinja2.Markup("file:///home/seanh/MyFile.pdf")

    assert isinstance(models.Annotation().filename, jinja2.Markup)


@patch("h.api.models.Annotation.uri", new_callable=PropertyMock)
def test_filename_with_FILE_uri(uri):
    uri.return_value = "FILE:///home/seanh/MyFile.pdf"

    assert models.Annotation().filename == "MyFile.pdf"


@patch("h.api.models.Annotation.uri", new_callable=PropertyMock)
def test_filename_with_folder(uri):
    uri.return_value = "file:///home/seanh/My%20Documents/"

    assert models.Annotation().filename == ""


@patch("h.api.models.Annotation.uri", new_callable=PropertyMock)
def test_filename_with_no_uri(uri):
    # self.uri should always be unicode, the worst is should ever be is an
    # empty string.
    uri.return_value = u""

    assert models.Annotation().filename == ""


@patch("h.api.models.Annotation.uri", new_callable=PropertyMock)
def test_filename_with_nonsense_uri(uri):
    uri.return_value = u"foobar"

    assert models.Annotation().filename == ""


title_fixtures = pytest.mark.usefixtures('uri', 'filename')


@title_fixtures
def test_title_with_a_document_that_has_a_title():
    """If the document has a title it should use it."""
    annotation = models.Annotation(document={'title': 'document title'})
    assert annotation.title == 'document title'


@title_fixtures
def test_title_escapes_html_in_document_titles():
    spam_link = '<a href="http://example.com/rubies">Buy rubies!!!</a>'
    annotation = models.Annotation(
        document={'title': '</a>' + spam_link})

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
    annotation = models.Annotation(document={})

    assert annotation.title == "MyFile.pdf"


@title_fixtures
def test_title_returns_Markup_when_filename_returns_Markup(filename):
    filename.return_value = jinja2.Markup("MyFile.pdf")
    annotation = models.Annotation(document={})

    assert isinstance(annotation.title, jinja2.Markup)


@title_fixtures
def test_title_unquotes_uris(uri, filename):
    filename.return_value = ""  # This is not a file:// URI.
    uri.return_value = "http://example.com/example%201.html"
    annotation = models.Annotation()

    assert annotation.title == "http://example.com/example 1.html"


@title_fixtures
def test_title_returns_Markup_when_uri_returns_Markup(uri, filename):
    filename.return_value = ""  # This is not a file:// URI.
    uri.return_value = jinja2.Markup("http://example.com/example.html")
    annotation = models.Annotation()

    assert isinstance(annotation.title, jinja2.Markup)


@title_fixtures
def test_title_when_document_has_None_for_title(uri, filename):
    """If the document has None for its title it should use the uri instead."""
    uri.return_value = "http://example.com/example.html"
    filename.return_value = ""  # This is not a file:// URI.
    annotation = models.Annotation(document={'title': None})

    assert annotation.title == "http://example.com/example.html"


@title_fixtures
def test_title_when_document_title_is_not_a_string(uri, filename):
    """If the document has None for its title it should use the uri instead."""
    uri.return_value = u"http://example.com/example.html"
    filename.return_value = ""  # This is not a file:// URI.

    for title in (23, 23.7, False, {"foo": "bar"}, [1, 2, 3]):
        annotation = models.Annotation(document={'title': title})
        assert isinstance(annotation.title, unicode)


@title_fixtures
def test_title_when_document_has_empty_string_for_title(uri, filename):
    """If the document has "" for its title it should use the uri instead."""
    uri.return_value = "http://example.com/example.html"
    filename.return_value = ""  # This is not a file:// URI.
    annotation = models.Annotation(document={'title': ""})

    assert annotation.title == "http://example.com/example.html"


@title_fixtures
def test_title_when_no_document_title_no_filename_and_no_uri(uri, filename):
    uri.return_value = ""
    filename.return_value = ""
    annotation = models.Annotation(document={})

    assert annotation.title == ""


@title_fixtures
def test_title_when_annotation_has_no_document_at_all(uri, filename):
    uri.return_value = "foo"
    filename.return_value = ""  # This is not a file:// URI.

    annotation = models.Annotation()

    assert annotation.title == "foo"


@title_fixtures
def test_title_when_annotations_document_is_not_a_dict(uri, filename):
    uri.return_value = "http://www.example.com/example.html"
    filename.return_value = ""  # This is not a file:// URI.

    for document in (False, 23, 12.7, None, [], [1, 2, 3], "foo", u"bar"):
        annotation = models.Annotation(document=document)
        assert annotation.title == uri.return_value


hostname_or_filename_fixtures = pytest.mark.usefixtures('uri', 'filename')


@hostname_or_filename_fixtures
def test_hostname_or_filename_returns_filename_for_files(filename):
    filename.return_value = "MyFile.pdf"
    annotation = models.Annotation()

    assert annotation.hostname_or_filename == "MyFile.pdf"


@hostname_or_filename_fixtures
def test_hostname_or_filename_returns_Markup_if_filename_does(filename):
    filename.return_value = jinja2.Markup("MyFile.pdf")
    annotation = models.Annotation()

    assert isinstance(annotation.hostname_or_filename, jinja2.Markup)


@hostname_or_filename_fixtures
def test_hostname_or_filename_returns_hostname_for_non_files(uri, filename):
    filename.return_value = ""
    uri.return_value = "http://www.example.com/example.html"
    annotation = models.Annotation()

    assert annotation.hostname_or_filename == "www.example.com"


@hostname_or_filename_fixtures
def test_hostname_or_filename_returns_Markup_when_uri_does(uri, filename):
    filename.return_value = ""
    uri.return_value = jinja2.Markup("http://www.example.com/example.html")
    annotation = models.Annotation()

    assert isinstance(annotation.hostname_or_filename, jinja2.Markup)


@hostname_or_filename_fixtures
def test_hostname_or_filename_with_empty_string_for_uri(uri, filename):
    filename.return_value = ""
    uri.return_value = u""
    annotation = models.Annotation()

    assert isinstance(annotation.hostname_or_filename, unicode)


@hostname_or_filename_fixtures
def test_hostname_or_filename_with_nonsense_uri(uri, filename):
    filename.return_value = ""

    # urlparse.urlparse(u"foobar").hostname is None, make sure this doesn't
    # trip up .hostname_or_filename.
    uri.return_value = u"foobar"

    annotation = models.Annotation()

    assert isinstance(annotation.hostname_or_filename, unicode)


href_fixtures = pytest.mark.usefixtures('uri')


@href_fixtures
def test_href_returns_uri_for_http_uri(uri):
    uri.return_value = "http://www.example.com/example.html"
    assert models.Annotation().href == uri.return_value


@href_fixtures
def test_href_returns_uri_for_https_uri(uri):
    uri.return_value = "https://www.example.com/example.html"
    assert models.Annotation().href == uri.return_value


@href_fixtures
def test_href_scheme_matching_is_case_insensitive(uri):
    for uri_ in (
            "HTTP://www.example.com/example.html",
            "HTTPS://www.example.com/example.html"):
        uri.return_value = uri_
        assert models.Annotation().href == uri_


@href_fixtures
def test_href_returns_empty_string_for_non_http_uris(uri):
    uri.return_value = "file:///MyFile.pdf"
    assert models.Annotation(uri=uri).href == ""


@href_fixtures
def test_href_returns_Markup_if_uri_returns_Markup(uri):
    uri.return_value = jinja2.Markup("http://www.example.com/example.html")
    assert isinstance(models.Annotation().href, jinja2.Markup)


link_text_fixtures = pytest.mark.usefixtures('title')


@link_text_fixtures
def test_link_text_with_non_http_title(title):
    """If .title doesn't start with http(s) link_text should just use it."""
    title.return_value = "Example Document"
    assert models.Annotation().link_text == "Example Document"


@link_text_fixtures
def test_link_text_with_http_title(title):
    """If .title is an http URI .link_test should use it.

    This happens when an annotation's document has no title, so .title falls
    back on the URI instead.

    """
    title.return_value = "http://www.example.com/example.html"
    assert models.Annotation().link_text == "www.example.com/example.html"


@link_text_fixtures
def test_link_text_with_https_title(title):
    """If .title is an https URI .link_test should use it.

    This happens when an annotation's document has no title, so .title falls
    back on the URI instead.

    """
    title.return_value = "https://www.example.com/example.html"
    assert models.Annotation().link_text == "www.example.com/example.html"


@link_text_fixtures
def test_link_text_returns_Markup_if_title_returns_Markup(title):
    for title_ in (
            jinja2.Markup("Example Document"),
            jinja2.Markup("http://www.example.com/example.html"),
            jinja2.Markup("https://www.example.com/example.html")):
        title.return_value = title_
        assert isinstance(models.Annotation().link_text, jinja2.Markup)


document_link_fixtures = pytest.mark.usefixtures(
    'link_text', 'title', 'href', 'hostname_or_filename')


@document_link_fixtures
def test_document_link_happy_path(hostname_or_filename, href, title,
                                  link_text):
    hostname_or_filename.return_value = "www.example.com"
    href.return_value = "http://www.example.com/example.html"
    title.return_value = "Example Document"
    link_text.return_value = "Example Document"

    assert models.Annotation().document_link == (
        '<a href="http://www.example.com/example.html" '
        'title="Example Document">Example Document</a> (www.example.com)')


@document_link_fixtures
def test_document_link_returns_Markup(hostname_or_filename, href, title,
                                      link_text):
    hostname_or_filename.return_value = "www.example.com"
    href.return_value = "http://www.example.com/example.html"
    title.return_value = "Example Document"
    link_text.return_value = "Example Document"

    assert isinstance(models.Annotation().document_link, jinja2.Markup)


@document_link_fixtures
def test_document_link_hostname_same_as_link_text(hostname_or_filename, href,
                                                  title, link_text):
    """If '(hostname)' is the same as the link text it shouldn't be shown."""
    href.return_value = "http://www.example.com"
    title.return_value = "www.example.com"

    # .hostname_or_filename and .link_text are the same.
    hostname_or_filename.return_value = "www.example.com"
    link_text.return_value = "www.example.com"

    assert models.Annotation().document_link == (
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

    assert models.Annotation().document_link == (
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
    hostname_or_filename.return_value = "a" * 60

    expected_hostname = "a" * 50 + "&hellip;"
    expected_result = (
        '<a href="http://www.example.com/example.html" '
        'title="www.example.com/example.html">'
        'www.example.com/example.html</a> ({hostname})'.format(
            hostname=expected_hostname))
    assert models.Annotation().document_link == expected_result


@document_link_fixtures
def test_document_link_truncates_link_text(hostname_or_filename, href, title,
                                           link_text):
    hostname_or_filename.return_value = "www.example.com"
    href.return_value = "http://www.example.com/example.html"
    title.return_value = "www.example.com/example.html"

    # .link_text is too long.
    link_text.return_value = "a" * 60

    expected_link_text = "a" * 50 + "&hellip;"
    expected_result = (
        '<a href="http://www.example.com/example.html" '
        'title="www.example.com/example.html">{link_text}</a> '
        '(www.example.com)'.format(link_text=expected_link_text))
    assert models.Annotation().document_link == expected_result


@document_link_fixtures
def test_document_link_hostname_but_no_href(hostname_or_filename, href, title,
                                            link_text):
    hostname_or_filename.return_value = "www.example.com"
    title.return_value = "Example Document"
    link_text.return_value = "Example Document"

    # No .href.
    href.return_value = ""

    assert models.Annotation().document_link == (
        '<a title="Example Document">Example Document</a> (www.example.com)')


@document_link_fixtures
def test_document_link_href_but_no_hostname(hostname_or_filename, href, title,
                                            link_text):
    href.return_value = "http://www.example.com/example.html"
    title.return_value = "www.example.com/example.html"
    link_text.return_value = "www.example.com/example.html"

    # No .hostname_or_filename.
    hostname_or_filename.return_value = ""

    assert models.Annotation().document_link == (
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

    assert models.Annotation().document_link == (
        '<a title="www.example.com/example.html">'
        'www.example.com/example.html</a>')


def test_description():
    annotation = models.Annotation(
        target=[{'selector': [{'exact': 'selected text'}]}],
        text='entered text'
    )

    assert annotation.description == (
        "&lt;blockquote&gt;selected text&lt;/blockquote&gt;entered text")


def test_created_day_string_from_annotation():
    annotation = models.Annotation(created='2015-09-04T17:37:49.517852+00:00')
    assert annotation.created_day_string == '2015-09-04'


def test_target_links_from_annotation():
    annotation = models.Annotation(target=[{'source': 'target link'}])
    assert annotation.target_links == ['target link']


def test_parent_returns_none_if_no_references():
    annotation = models.Annotation()
    assert annotation.parent is None


def test_parent_returns_none_if_empty_references():
    annotation = models.Annotation(references=[])
    assert annotation.parent is None


def test_parent_returns_none_if_references_not_list():
    annotation = models.Annotation(references={'foo': 'bar'})
    assert annotation.parent is None


@patch.object(models.Annotation, 'fetch', spec=True)
def test_parent_fetches_thread_parent(fetch):
    annotation = models.Annotation(references=['abc123', 'def456'])
    annotation.parent
    fetch.assert_called_with('def456')


@patch.object(models.Annotation, 'fetch', spec=True)
def test_parent_returns_thread_parent(fetch):
    annotation = models.Annotation(references=['abc123', 'def456'])
    parent = annotation.parent
    assert parent == fetch.return_value


@pytest.fixture
def link_text(request):
    patcher = patch('h.api.models.Annotation.link_text',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def title(request):
    patcher = patch('h.api.models.Annotation.title',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()

@pytest.fixture
def href(request):
    patcher = patch('h.api.models.Annotation.href',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def hostname_or_filename(request):
    patcher = patch('h.api.models.Annotation.hostname_or_filename',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def uri(request):
    patcher = patch('h.api.models.Annotation.uri', new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def filename(request):
    patcher = patch('h.api.models.Annotation.filename',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()
