# -*- coding: utf-8 -*-

import pytest

from h import models
from h.presenters.document_searchindex import DocumentSearchIndexPresenter


class TestDocumentSearchIndexPresenter:
    @pytest.mark.parametrize(
        "document,expected",
        [
            (models.Document(title="Foo"), {"title": ["Foo"]}),
            (models.Document(title=""), {}),
            (models.Document(title=None), {}),
            (models.Document(web_uri="http://foo.org"), {"web_uri": "http://foo.org"}),
            (models.Document(web_uri=""), {}),
            (models.Document(web_uri=None), {}),
            (
                models.Document(title="Foo", web_uri="http://foo.org"),
                {"title": ["Foo"], "web_uri": "http://foo.org"},
            ),
            (None, {}),
        ],
    )
    def test_asdict(self, document, expected):
        assert expected == DocumentSearchIndexPresenter(document).asdict()
