# -*- coding: utf-8 -*-

import pytest

from h import links


class FakeAnnotation(object):
    def __init__(self):
        self.thread_root_id = '123'
        self.references = None
        self.target_uri = 'http://example.com/foo/bar'
        self.document = None


class FakeDocumentURI(object):
    def __init__(self):
        self.uri = 'http://example.com/foo.pdf'


class FakeDocument(object):
    def __init__(self):
        self.document_uris = []


def test_incontext_link(pyramid_request):
    annotation = FakeAnnotation()

    link = links.incontext_link(pyramid_request, annotation)

    assert link == 'https://hyp.is/123/example.com/foo/bar'


@pytest.mark.parametrize('target_uri,expected', [
    ('', 'https://hyp.is/123'),
    ('something_not_a_url', 'https://hyp.is/123'),
    ('ftp://not_http', 'https://hyp.is/123'),
    ('http://example.com/foo/bar', 'https://hyp.is/123/example.com/foo/bar'),
    ('https://safari.org/giraffes', 'https://hyp.is/123/safari.org/giraffes'),
])
def test_incontext_link_appends_schemaless_uri_if_present(pyramid_request,
                                                          target_uri,
                                                          expected):
    annotation = FakeAnnotation()
    annotation.target_uri = target_uri

    link = links.incontext_link(pyramid_request, annotation)

    assert link == expected


def test_incontext_link_appends_first_schemaless_uri_for_pdfs_with_document(pyramid_request):
    doc = FakeDocument()
    docuri1 = FakeDocumentURI()
    docuri1.uri = 'http://example.com/foo.pdf'
    docuri2 = FakeDocumentURI()
    docuri2.uri = 'http://example.com/bar.pdf'

    doc.document_uris = [docuri1, docuri2]

    annotation = FakeAnnotation()
    annotation.document = doc
    annotation.target_uri = 'urn:x-pdf:the-fingerprint'

    link = links.incontext_link(pyramid_request, annotation)

    assert link == 'https://hyp.is/123/example.com/foo.pdf'


def test_incontext_link_skips_uri_for_pdfs_with_no_document(pyramid_request):
    annotation = FakeAnnotation()
    annotation.target_uri = 'urn:x-pdf:the-fingerprint'

    link = links.incontext_link(pyramid_request, annotation)

    assert link == 'https://hyp.is/123'


@pytest.mark.parametrize('uri,formatted', [
    ('http://notsecure.com', 'notsecure.com'),
    ('https://secure.com', 'secure.com'),
    ('ftp://not_http', 'ftp://not_http'),
    ('http://www.google.com', 'google.com'),
    ('http://site.com/with-a-path', 'site.com/with-a-path'),
    ('https://site.com/with-a-path?q=and-a-query-string', 'site.com/with-a-path'),
    ('http://site.com/path%20with%20spaces','site.com/path with spaces'),
    ('', ''),
    ('site.com/no-scheme', 'site.com/no-scheme'),
    ('does not look like a URL', 'does not look like a URL'),
])
def test_pretty_link(uri, formatted):
    assert links.pretty_link(uri) == formatted


@pytest.fixture
def pyramid_settings(pyramid_settings):
    pyramid_settings.update({
        'h.bouncer_url': 'https://hyp.is',
    })
    return pyramid_settings
