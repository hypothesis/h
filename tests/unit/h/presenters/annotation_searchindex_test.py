import pytest
from h_matchers import Any

from h.presenters.annotation_searchindex import AnnotationSearchIndexPresenter
from h.util.datetime import utc_iso8601

pytestmark = pytest.mark.usefixtures("moderation_service")


@pytest.mark.usefixtures("nipsa_service")
class TestAnnotationSearchIndexPresenter:
    def test_asdict(self, DocumentSearchIndexPresenter, pyramid_request, factories):
        annotation = factories.Annotation(
            references=[
                reference.id for reference in factories.Annotation.create_batch(2)
            ]
        )
        replies = factories.Annotation.create_batch(2, references=[annotation.id])

        annotation_dict = AnnotationSearchIndexPresenter(
            annotation, pyramid_request
        ).asdict()

        assert annotation_dict == {
            "authority": annotation.authority,
            "id": annotation.id,
            "created": utc_iso8601(annotation.created),
            "updated": utc_iso8601(annotation.updated),
            "user": annotation.userid,
            "user_raw": annotation.userid,
            "uri": annotation.target_uri,
            "text": annotation.text,
            "tags": annotation.tags,
            "tags_raw": annotation.tags,
            "group": annotation.groupid,
            "shared": annotation.shared,
            "target": [
                {"scope": [annotation.target_uri_normalized], **annotation.target[0]}
            ],
            "document": DocumentSearchIndexPresenter.return_value.asdict.return_value,
            "references": annotation.references,
            "thread_ids": Any.list.containing([reply.id for reply in replies]).only(),
            "hidden": False,
        }

    @pytest.mark.parametrize("is_moderated", [True, False])
    @pytest.mark.parametrize("replies_moderated", [True, False])
    def test_it_marks_annotation_hidden_correctly(
        self,
        pyramid_request,
        moderation_service,
        is_moderated,
        replies_moderated,
        factories,
    ):
        annotation = factories.Annotation()
        replies = factories.Annotation.create_batch(2, references=[annotation.id])

        # Configure moderation return value
        moderated_ids = []
        if is_moderated:
            moderated_ids.append(annotation.id)
        if replies_moderated:
            moderated_ids.extend([reply.id for reply in replies])
        moderation_service.all_hidden.return_value = moderated_ids

        annotation_dict = AnnotationSearchIndexPresenter(
            annotation, pyramid_request
        ).asdict()

        # We are hidden if both we, and all of our replies are moderated
        assert annotation_dict["hidden"] == bool(is_moderated and replies_moderated)

    @pytest.mark.parametrize("is_nipsaed", [True, False])
    def test_it_marks_annotation_nipsad_correctly(
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
