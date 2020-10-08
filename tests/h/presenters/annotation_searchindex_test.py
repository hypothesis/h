import datetime
from unittest import mock

import pytest

from h.presenters.annotation_searchindex import AnnotationSearchIndexPresenter


@pytest.mark.usefixtures("nipsa_service")
class TestAnnotationSearchIndexPresenter:
    def test_asdict(self, DocumentSearchIndexPresenter, pyramid_request, factories):
        annotation = mock.MagicMock(
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

        annotation_dict = AnnotationSearchIndexPresenter(
            annotation, pyramid_request
        ).asdict()

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
            "hidden": False,
        }

    @pytest.mark.parametrize("is_moderated", [True, False])
    @pytest.mark.parametrize("replies_moderated", [True, False])
    def test_it_marks_annotation_hidden_correctly(
        self, pyramid_request, moderation_service, is_moderated, replies_moderated
    ):
        # Annotation reply ids are referred to as thread_ids in our code base.
        reply_ids = ["thread-id-1", "thread-id-2"]

        annotation = mock.MagicMock(
            userid="acct:luke@hypothes.is", thread_ids=reply_ids
        )

        # Configure moderation return value
        moderated_ids = []
        if is_moderated:
            moderated_ids.append(annotation.id)
        if replies_moderated:
            moderated_ids.extend(reply_ids)
        moderation_service.all_hidden.return_value = moderated_ids

        annotation_dict = AnnotationSearchIndexPresenter(
            annotation, pyramid_request
        ).asdict()

        # We are hidden if both we, and all of our replies are moderated
        assert annotation_dict["hidden"] == bool(is_moderated and replies_moderated)

    @pytest.mark.parametrize("is_nipsaed", [True, False])
    def test_it_marks_annotation_nipsaed_correctly(
        self, pyramid_request, nipsa_service, is_nipsaed, factories
    ):
        annotation = factories.Annotation.build()
        nipsa_service.is_flagged.return_value = is_nipsaed

        annotation_dict = AnnotationSearchIndexPresenter(
            annotation, pyramid_request
        ).asdict()

        if is_nipsaed:
            assert annotation_dict["nipsa"]
        else:
            assert "nipsa" not in annotation_dict

    @pytest.fixture(autouse=True)
    def DocumentSearchIndexPresenter(self, patch):
        class_ = patch(
            "h.presenters.annotation_searchindex.DocumentSearchIndexPresenter"
        )
        class_.return_value.asdict.return_value = {}
        return class_


pytestmark = pytest.mark.usefixtures("moderation_service")
