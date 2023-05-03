import pytest

from h import storage
from h.models.document import Document, DocumentURI


@pytest.mark.usefixtures("search_index")
class TestExpandURI:
    @pytest.mark.parametrize(
        "normalized,expected_uris",
        (
            (False, ["http://example.com/"]),
            (True, ["httpx://example.com"]),
        ),
    )
    def test_expand_uri_no_document(self, db_session, normalized, expected_uris):
        uris = storage.expand_uri(
            db_session, "http://example.com/", normalized=normalized
        )

        assert uris == expected_uris

    @pytest.mark.parametrize(
        "normalized,expected_uris",
        (
            (False, ["http://example.com/"]),
            (True, ["httpx://example.com"]),
        ),
    )
    def test_expand_uri_document_doesnt_expand_canonical_uris(
        self, db_session, normalized, expected_uris
    ):
        document = Document(
            document_uris=[
                DocumentURI(
                    uri="http://example.com/",
                    type="rel-canonical",
                    claimant="http://example.com",
                ),
                DocumentURI(
                    uri="http://noise.example.com/", claimant="http://example.com"
                ),
            ]
        )
        db_session.add(document)
        db_session.flush()

        uris = storage.expand_uri(
            db_session, "http://example.com/", normalized=normalized
        )

        assert uris == expected_uris

    @pytest.mark.parametrize(
        "normalized,expected_uris",
        (
            (False, ["http://example.com/", "http://alt.example.com/"]),
            (True, ["httpx://example.com", "httpx://alt.example.com"]),
        ),
    )
    def test_expand_uri_document_uris(self, db_session, normalized, expected_uris):
        document = Document(
            document_uris=[
                DocumentURI(uri="http://example.com/", claimant="http://example.com"),
                DocumentURI(
                    uri="http://alt.example.com/", claimant="http://example.com"
                ),
            ]
        )
        db_session.add(document)
        db_session.flush()

        uris = storage.expand_uri(
            db_session, "http://alt.example.com/", normalized=normalized
        )

        assert uris == expected_uris
