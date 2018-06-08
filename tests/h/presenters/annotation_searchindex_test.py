# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import mock
import pytest

from h.presenters.annotation_searchindex import AnnotationSearchIndexPresenter


@pytest.mark.usefixtures("DocumentSearchIndexPresenter")
class TestAnnotationSearchIndexPresenter(object):
    def test_asdict(self, DocumentSearchIndexPresenter):
        annotation = mock.Mock(
            id="xyz123",
            created=datetime.datetime(2016, 2, 24, 18, 3, 25, 768),
            updated=datetime.datetime(2016, 2, 29, 10, 24, 5, 564),
            userid="acct:luke@hypothes.is",
            target_uri="http://example.com",
            target_uri_normalized="http://example.com/normalized",
            text="It is magical!",
            tags=["magic"],
            groupid="__world__",
            shared=True,
            target_selectors=[{"TestSelector": "foobar"}],
            references=["referenced-id-1", "referenced-id-2"],
            thread_ids=["thread-id-1", "thread-id-2"],
            extra={"extra-1": "foo", "extra-2": "bar"},
        )
        DocumentSearchIndexPresenter.return_value.asdict.return_value = {"foo": "bar"}

        annotation_dict = AnnotationSearchIndexPresenter(annotation).asdict()

        assert annotation_dict == {
            "authority": "hypothes.is",
            "id": "xyz123",
            "created": "2016-02-24T18:03:25.000768+00:00",
            "updated": "2016-02-29T10:24:05.000564+00:00",
            "user": "acct:luke@hypothes.is",
            "user_raw": "acct:luke@hypothes.is",
            "uri": "http://example.com",
            "text": "It is magical!",
            "tags": ["magic"],
            "tags_raw": ["magic"],
            "group": "__world__",
            "shared": True,
            "target": [
                {
                    "scope": ["http://example.com/normalized"],
                    "source": "http://example.com",
                    "selector": [{"TestSelector": "foobar"}],
                }
            ],
            "document": {"foo": "bar"},
            "references": ["referenced-id-1", "referenced-id-2"],
            "thread_ids": ["thread-id-1", "thread-id-2"],
        }

    def test_it_copies_target_uri_normalized_to_target_scope(self):
        annotation = mock.Mock(
            userid="acct:luke@hypothes.is",
            target_uri_normalized="http://example.com/normalized",
            extra={},
        )

        annotation_dict = AnnotationSearchIndexPresenter(annotation).asdict()

        assert annotation_dict["target"][0]["scope"] == [
            "http://example.com/normalized"
        ]

    @pytest.fixture
    def DocumentSearchIndexPresenter(self, patch):
        class_ = patch(
            "h.presenters.annotation_searchindex.DocumentSearchIndexPresenter"
        )
        class_.return_value.asdict.return_value = {}
        return class_
