from datetime import datetime  # noqa: INP001
from unittest.mock import sentinel

import pytest

from h.services.bulk_api.lms_stats import (
    AnnotationCounts,
    BulkLMSStatsService,
    CountsGroupBy,
    service_factory,
)


class TestBulkLMSStatsService:
    @pytest.mark.usefixtures("annotation_in_another_assignment")
    def test_get_annotation_counts_by_user(
        self, svc, group, user, annotation, annotation_reply, reply_user
    ):
        stats = svc.get_annotation_counts(
            groups=[group.authority_provided_id],
            assignment_ids=["ASSIGNMENT_ID"],
            group_by=CountsGroupBy.USER,
        )

        assert len(stats) == 2
        assert (
            AnnotationCounts(
                userid=user.userid,
                display_name=user.display_name,
                annotations=1,
                replies=0,
                page_notes=0,
                last_activity=annotation.created,
            )
            in stats
        )
        assert (
            AnnotationCounts(
                userid=reply_user.userid,
                display_name=reply_user.display_name,
                annotations=0,
                replies=1,
                page_notes=0,
                last_activity=annotation_reply.created,
            )
            in stats
        )

    @pytest.mark.usefixtures("annotation", "user", "reply_user", "page_note")
    def test_get_annotation_counts_by_assignment(
        self,
        svc,
        group,
        annotation_reply,
        annotation_in_another_assignment,
    ):
        stats = svc.get_annotation_counts(
            groups=[group.authority_provided_id], group_by=CountsGroupBy.ASSIGNMENT
        )

        assert len(stats) == 2
        assert (
            AnnotationCounts(
                assignment_id="ASSIGNMENT_ID",
                annotations=1,
                replies=1,
                page_notes=1,
                last_activity=annotation_reply.created,
            )
            in stats
        )
        assert (
            AnnotationCounts(
                assignment_id="OTHER_ASSIGNMENT_ID",
                annotations=1,
                replies=0,
                page_notes=0,
                last_activity=annotation_in_another_assignment.created,
            )
            in stats
        )

    @pytest.mark.usefixtures("annotation", "user", "reply_user")
    def test_get_annotation_counts_filter_by_h_userids(
        self,
        svc,
        group,
        annotation_reply,
        annotation_in_another_assignment,  # noqa: ARG002
        reply_user,
    ):
        stats = svc.get_annotation_counts(
            groups=[group.authority_provided_id],
            group_by=CountsGroupBy.ASSIGNMENT,
            h_userids=[reply_user.userid],
        )

        assert stats == [
            AnnotationCounts(
                assignment_id="ASSIGNMENT_ID",
                annotations=0,
                replies=1,
                page_notes=0,
                last_activity=annotation_reply.created,
            ),
        ]

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def reply_user(self, factories):
        return factories.User()

    @pytest.fixture
    def annotation(self, factories, user, group):
        anno = factories.Annotation(group=group)
        anno_slim = factories.AnnotationSlim(
            annotation=anno,
            user=user,
            deleted=False,
            shared=True,
            moderated=False,
            group=group,
        )
        factories.AnnotationMetadata(
            annotation_slim=anno_slim,
            data={"lms": {"assignment": {"resource_link_id": "ASSIGNMENT_ID"}}},
        )

        return anno_slim

    @pytest.fixture
    def page_note(self, factories, user, group):
        anno = factories.Annotation(group=group, target_selectors=[])
        anno_slim = factories.AnnotationSlim(
            annotation=anno,
            user=user,
            deleted=False,
            shared=True,
            moderated=False,
            group=group,
        )
        factories.AnnotationMetadata(
            annotation_slim=anno_slim,
            data={"lms": {"assignment": {"resource_link_id": "ASSIGNMENT_ID"}}},
        )

        return anno_slim

    @pytest.fixture
    def annotation_in_another_assignment(self, factories, user, group):
        anno = factories.Annotation(group=group)
        anno_slim = factories.AnnotationSlim(
            annotation=anno,
            user=user,
            deleted=False,
            shared=True,
            moderated=False,
            group=group,
        )
        factories.AnnotationMetadata(
            annotation_slim=anno_slim,
            data={"lms": {"assignment": {"resource_link_id": "OTHER_ASSIGNMENT_ID"}}},
        )

        return anno_slim

    @pytest.fixture
    def annotation_reply(self, factories, reply_user, group, annotation):
        anno_reply = factories.Annotation(group=group, references=[annotation.pubid])
        anno_slim_reply = factories.AnnotationSlim(
            annotation=anno_reply,
            user=reply_user,
            deleted=False,
            shared=True,
            moderated=False,
            group=group,
        )
        factories.AnnotationMetadata(
            annotation_slim=anno_slim_reply,
            data={"lms": {"assignment": {"resource_link_id": "ASSIGNMENT_ID"}}},
        )

        return anno_slim_reply

    @pytest.fixture
    def svc(self, db_session):
        return BulkLMSStatsService(db_session, "example.com")


class TestBulkLMSStatsServiceCheckpoint:
    def test_get_annotation_counts_splits_checkpoint_bucket(
        self, svc, factories, group, user, document_uri
    ):
        reveal_date = datetime(2024, 6, 1)  # noqa: DTZ001
        factories.Checkpoint(
            group=group, document=document_uri.document, reveal_date=reveal_date
        )
        self._make_annotation(
            factories,
            group,
            user,
            datetime(2024, 5, 1),  # noqa: DTZ001
        )
        self._make_annotation(
            factories,
            group,
            user,
            datetime(2024, 7, 1),  # noqa: DTZ001
        )

        stats = svc.get_annotation_counts(
            groups=[group.authority_provided_id],
            assignment_ids=["ASSIGNMENT_ID"],
            group_by=CountsGroupBy.USER_PHASE,
            document_uri=document_uri.uri,
        )

        assert [(row.phase, row.annotations) for row in stats] == [(1, 1), (2, 1)]
        assert stats[0].ends_at == reveal_date

    def test_get_annotation_counts_unrevealed_checkpoint_counts_everything_as_checkpoint(
        self, svc, factories, group, user, document_uri
    ):
        factories.Checkpoint(
            group=group, document=document_uri.document, reveal_date=None
        )
        self._make_annotation(
            factories,
            group,
            user,
            datetime(2024, 5, 1),  # noqa: DTZ001
        )

        stats = svc.get_annotation_counts(
            groups=[group.authority_provided_id],
            assignment_ids=["ASSIGNMENT_ID"],
            group_by=CountsGroupBy.USER_PHASE,
            document_uri=document_uri.uri,
        )

        # Nothing has left the first phase, and its boundary isn't known yet.
        assert [(row.phase, row.annotations) for row in stats] == [(1, 1), (2, 0)]
        assert stats[0].ends_at is None

    def test_get_annotation_counts_document_uri_requires_single_assignment_id(
        self, svc, group, document_uri
    ):
        with pytest.raises(ValueError, match="exactly one"):
            svc.get_annotation_counts(
                groups=[group.authority_provided_id],
                assignment_ids=["ASSIGNMENT_1", "ASSIGNMENT_2"],
                group_by=CountsGroupBy.USER,
                document_uri=document_uri.uri,
            )

    def test_get_annotation_counts_document_uri_requires_an_assignment_id(
        self, svc, group, document_uri
    ):
        with pytest.raises(ValueError, match="exactly one"):
            svc.get_annotation_counts(
                groups=[group.authority_provided_id],
                assignment_ids=None,
                group_by=CountsGroupBy.USER,
                document_uri=document_uri.uri,
            )

    def test_get_annotation_counts_without_document_uri_leaves_checkpoint_fields_none(
        self,
        svc,
        group,
        annotation,  # noqa: ARG002
    ):
        stats = svc.get_annotation_counts(
            groups=[group.authority_provided_id],
            assignment_ids=["ASSIGNMENT_ID"],
            group_by=CountsGroupBy.USER,
        )

        assert stats[0].phase is None
        assert stats[0].ends_at is None

    def test_get_annotation_counts_due_date_bounds_all_counts(
        self, svc, factories, group, user
    ):
        self._make_annotation(
            factories,
            group,
            user,
            datetime(2024, 1, 1),  # noqa: DTZ001
        )
        self._make_annotation(
            factories,
            group,
            user,
            datetime(2024, 3, 1),  # noqa: DTZ001
        )

        stats = svc.get_annotation_counts(
            groups=[group.authority_provided_id],
            assignment_ids=["ASSIGNMENT_ID"],
            group_by=CountsGroupBy.USER,
            due_date=datetime(2024, 2, 1),  # noqa: DTZ001
        )

        assert len(stats) == 1
        assert stats[0].annotations == 1

    def test_get_annotation_counts_uses_each_groups_own_reveal_date(
        self, svc, factories, user, document_uri
    ):
        # A group set reveals the same assignment per group, at different times.
        early_group, late_group = factories.Group.create_batch(2)
        factories.Checkpoint(
            group=early_group,
            document=document_uri.document,
            reveal_date=datetime(2024, 6, 1),  # noqa: DTZ001
        )
        factories.Checkpoint(
            group=late_group,
            document=document_uri.document,
            reveal_date=datetime(2024, 8, 1),  # noqa: DTZ001
        )
        # The same date, either side of each group's own reveal.
        annotated = datetime(2024, 7, 1)  # noqa: DTZ001
        self._make_annotation(factories, early_group, user, annotated)
        self._make_annotation(factories, late_group, user, annotated)

        stats = svc.get_annotation_counts(
            groups=[
                early_group.authority_provided_id,
                late_group.authority_provided_id,
            ],
            assignment_ids=["ASSIGNMENT_ID"],
            group_by=CountsGroupBy.USER_PHASE,
            document_uri=document_uri.uri,
        )

        # Only the annotation in the group revealed later is still in its first
        # phase. Collapsing both groups to one reveal date would put either
        # both or neither there.
        assert [(row.phase, row.annotations) for row in stats] == [(1, 1), (2, 1)]

    def test_get_annotation_counts_with_a_scheduled_reveal_counts_everything_as_checkpoint(
        self, svc, factories, group, user, document_uri
    ):
        # h supports a reveal_date in the future: the checkpoint is still
        # hiding, so nothing has left the first phase yet.
        factories.Checkpoint(
            group=group,
            document=document_uri.document,
            reveal_date=datetime(2099, 1, 1),  # noqa: DTZ001
        )
        self._make_annotation(factories, group, user, datetime(2024, 5, 1))  # noqa: DTZ001

        stats = svc.get_annotation_counts(
            groups=[group.authority_provided_id],
            assignment_ids=["ASSIGNMENT_ID"],
            group_by=CountsGroupBy.USER_PHASE,
            document_uri=document_uri.uri,
        )

        assert [(row.phase, row.annotations) for row in stats] == [(1, 1), (2, 0)]

    def test_get_annotation_counts_with_no_checkpoint_for_the_group(
        self, svc, factories, group, user, document_uri
    ):
        # No checkpoint at all: nothing has been revealed, so everything is
        # still in the first phase.
        self._make_annotation(factories, group, user, datetime(2024, 5, 1))  # noqa: DTZ001

        stats = svc.get_annotation_counts(
            groups=[group.authority_provided_id],
            assignment_ids=["ASSIGNMENT_ID"],
            group_by=CountsGroupBy.USER_PHASE,
            document_uri=document_uri.uri,
        )

        assert [(row.phase, row.annotations) for row in stats] == [(1, 1), (2, 0)]
        assert stats[0].ends_at is None

    def test_get_annotation_counts_user_phase_requires_a_document_uri(self, svc, group):
        with pytest.raises(ValueError, match="USER_PHASE requires document_uri"):
            svc.get_annotation_counts(
                groups=[group.authority_provided_id],
                assignment_ids=["ASSIGNMENT_ID"],
                group_by=CountsGroupBy.USER_PHASE,
            )

    @staticmethod
    def _make_annotation(factories, group, user, created):
        anno = factories.Annotation(group=group, created=created)
        anno_slim = factories.AnnotationSlim(
            annotation=anno,
            user=user,
            group=group,
            deleted=False,
            shared=True,
            moderated=False,
            created=created,
        )
        factories.AnnotationMetadata(
            annotation_slim=anno_slim,
            data={"lms": {"assignment": {"resource_link_id": "ASSIGNMENT_ID"}}},
        )
        return anno_slim

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def document_uri(self, factories):
        uri = "http://example.com/reading"
        return factories.DocumentURI(uri=uri, claimant=uri)

    @pytest.fixture
    def annotation(self, factories, user, group):
        anno = factories.Annotation(group=group)
        anno_slim = factories.AnnotationSlim(
            annotation=anno,
            user=user,
            deleted=False,
            shared=True,
            moderated=False,
            group=group,
        )
        factories.AnnotationMetadata(
            annotation_slim=anno_slim,
            data={"lms": {"assignment": {"resource_link_id": "ASSIGNMENT_ID"}}},
        )
        return anno_slim

    @pytest.fixture
    def svc(self, db_session):
        return BulkLMSStatsService(db_session, "example.com")


class TestServiceFactory:
    @pytest.mark.usefixtures("with_auth_client")
    def test_it(self, pyramid_request, BulkLMSStatsService):
        svc = service_factory(sentinel.context, pyramid_request)

        BulkLMSStatsService.assert_called_once_with(
            db=pyramid_request.db,
            authorized_authority=pyramid_request.identity.auth_client.authority,
        )
        assert svc == BulkLMSStatsService.return_value

    @pytest.fixture
    def BulkLMSStatsService(self, patch):
        return patch("h.services.bulk_api.lms_stats.BulkLMSStatsService")
