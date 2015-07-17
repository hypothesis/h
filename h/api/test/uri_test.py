import pytest
from mock import patch

from h.api import uri


@pytest.mark.parametrize("url_in,url_out", [
    ("urn:doi:10.0001/12345", "urn:doi:10.0001/12345"),
    ("http://example.com/", "http://example.com/"),
    ("https://foo.bar.org/", "https://foo.bar.org/"),
])
def test_normalise(url_in, url_out):
    assert uri.normalise(url_in) == url_out


def test_expand_no_document(document_model):
    document_model.get_by_uri.return_value = None
    assert uri.expand("http://example.com/") == ["http://example.com/"]


def test_expand_document_uris(document_model):
    document_model.get_by_uri.return_value.uris.return_value = [
        "http://foo.com/",
        "http://bar.com/",
    ]
    assert uri.expand("http://example.com/") == [
        "http://foo.com/",
        "http://bar.com/",
    ]


@pytest.fixture
def document_model(config, request):
    patcher = patch('h.api.models.Document', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
