import pytest

from h.models import Document
from h.presenters.document_json import DocumentJSONPresenter


class TestDocumentJSONPresenter:
    @pytest.mark.parametrize(
        "document,expected",
        ((Document(title="TITLE"), {"title": ["TITLE"]}), (Document(), {}), (None, {})),
    )
    def test_asdict(self, document, expected):
        assert DocumentJSONPresenter(document).asdict() == expected
