from unittest import mock

import pytest

from h import links, models


class FakeAnnotation:
    def __init__(self):
        self.thread_root_id = "123"
        self.references = None
        self.target_uri = "http://example.com/foo/bar"
        self.document = None


class FakeDocumentURI:
    def __init__(self):
        self.uri = "http://example.com/foo.pdf"


class FakeDocument:
    def __init__(self):
        self.document_uris = []


@pytest.mark.usefixtures("routes")
class TestHTMLLink:
    def test_html_link_returns_links_for_first_party_annotations(
        self, annotation, pyramid_request
    ):
        # Specify the authority so that it's a first-party annotation.
        annotation.authority = pyramid_request.default_authority

        link = links.html_link(pyramid_request, annotation)

        assert link == "http://example.com/a/ANNOTATION_ID"

    def test_html_link_returns_None_for_third_party_annotations(
        self, annotation, pyramid_request
    ):
        # Specify the authority so that it's a third-party annotation.
        annotation.authority = "elifesciences.org"

        assert links.html_link(pyramid_request, annotation) is None

    @pytest.fixture
    def annotation(self):
        return mock.create_autospec(
            models.Annotation, spec_set=True, instance=True, id="ANNOTATION_ID"
        )

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("annotation", "/a/{id}")


def test_incontext_link(pyramid_request):
    annotation = FakeAnnotation()

    link = links.incontext_link(pyramid_request, annotation)

    assert link == "https://hyp.is/123/example.com/foo/bar"


@pytest.mark.parametrize(
    "target_uri,expected",
    [
        ("", "https://hyp.is/123"),
        ("something_not_a_url", "https://hyp.is/123"),
        ("ftp://not_http", "https://hyp.is/123"),
        ("http://example.com/foo/bar", "https://hyp.is/123/example.com/foo/bar"),
        ("https://safari.org/giraffes", "https://hyp.is/123/safari.org/giraffes"),
    ],
)
def test_incontext_link_appends_schemaless_uri_if_present(
    pyramid_request, target_uri, expected
):
    annotation = FakeAnnotation()
    annotation.target_uri = target_uri

    link = links.incontext_link(pyramid_request, annotation)

    assert link == expected


def test_incontext_link_appends_first_schemaless_uri_for_pdfs_with_document(
    pyramid_request,
):
    doc = FakeDocument()
    docuri1 = FakeDocumentURI()
    docuri1.uri = "http://example.com/foo.pdf"
    docuri2 = FakeDocumentURI()
    docuri2.uri = "http://example.com/bar.pdf"

    doc.document_uris = [docuri1, docuri2]

    annotation = FakeAnnotation()
    annotation.document = doc
    annotation.target_uri = "urn:x-pdf:the-fingerprint"

    link = links.incontext_link(pyramid_request, annotation)

    assert link == "https://hyp.is/123/example.com/foo.pdf"


def test_incontext_link_skips_uri_for_pdfs_with_no_document(pyramid_request):
    annotation = FakeAnnotation()
    annotation.target_uri = "urn:x-pdf:the-fingerprint"

    link = links.incontext_link(pyramid_request, annotation)

    assert link == "https://hyp.is/123"


def test_json_link(factories, pyramid_config, pyramid_request):
    annotation = factories.Annotation(id="e22AJlHYQNCG70bXL7gr1w")
    pyramid_config.add_route("api.annotation", "/annos/{id}")

    link = links.json_link(pyramid_request, annotation)

    assert link == "http://example.com/annos/e22AJlHYQNCG70bXL7gr1w"


def test_jsonld_id_link(factories, pyramid_config, pyramid_request):
    annotation = factories.Annotation(id="e22AJlHYQNCG70bXL7gr1w")
    pyramid_config.add_route("annotation", "/annos/{id}")

    link = links.jsonld_id_link(pyramid_request, annotation)

    assert link == "http://example.com/annos/e22AJlHYQNCG70bXL7gr1w"


@pytest.mark.parametrize(
    "uri,formatted",
    [
        ("http://notsecure.com", "notsecure.com"),
        ("https://secure.com", "secure.com"),
        ("ftp://not_http", "ftp://not_http"),
        ("http://www.google.com", "google.com"),
        ("http://site.com/with-a-path", "site.com/with-a-path"),
        ("https://site.com/with-a-path?q=and-a-query-string", "site.com/with-a-path"),
        ("http://site.com/path%20with%20spaces", "site.com/path with spaces"),
        ("", ""),
        ("site.com/no-scheme", "site.com/no-scheme"),
        ("does not look like a URL", "does not look like a URL"),
    ],
)
def test_pretty_link(uri, formatted):
    assert links.pretty_link(uri) == formatted


@pytest.fixture
def pyramid_settings(pyramid_settings):
    pyramid_settings.update({"h.bouncer_url": "https://hyp.is"})
    return pyramid_settings
