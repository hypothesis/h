# -*- coding: utf-8 -*-
import pytest

from h.api import validators


def test_Annotation_returns_None_for_valid_data():
    data = {"document": {"link": ["http://example.com/example"]}}

    assert validators.Annotation().validate(data) is None


def test_Annotation_raises_if_document_link_is_None():
    data = {"document": {"link": None}}  # Invalid link.

    with pytest.raises(validators.Error):
        validators.Annotation().validate(data)
