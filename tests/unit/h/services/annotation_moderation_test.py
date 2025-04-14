import pytest

from h.models.annotation import ModerationStatus
from h.services.annotation_moderation import (
    AnnotationModerationService,
    annotation_moderation_service_factory,
)


class TestAnnotationModerationService:
    def test_all_hidden_lists_moderated_annotation_ids(
        self, svc, moderated_annotations
    ):
        ids = [a.id for a in moderated_annotations[0:-1]]
        assert svc.all_hidden(ids) == set(ids)

    def test_all_hidden_skips_non_moderated_annotations(self, svc, factories):
        annotation = factories.Annotation()

        assert svc.all_hidden([annotation.id]) == set()

    def test_all_hidden_handles_with_no_ids(self, svc):
        assert svc.all_hidden([]) == set()

    def test_set_status_with_None_status_doesnt_change_it(self, svc, annotation, user):
        annotation.moderation_status = ModerationStatus.APPROVED

        svc.set_status(annotation, user, None)

        assert annotation.moderation_status is ModerationStatus.APPROVED

    def test_set_status_with_same_status_doesnt_change_it(self, svc, annotation, user):
        annotation.moderation_status = ModerationStatus.APPROVED

        svc.set_status(annotation, user, ModerationStatus.APPROVED)

        assert annotation.moderation_status is ModerationStatus.APPROVED
        assert annotation.moderation_log == []

    def test_set_status(self, svc, annotation, user):
        annotation.moderation_status = ModerationStatus.APPROVED

        svc.set_status(annotation, user, ModerationStatus.DENIED)

        assert annotation.moderation_status is ModerationStatus.DENIED
        assert annotation.moderation_log[0].annotation_id == annotation.id
        assert annotation.moderation_log[0].user_id == user.id
        assert (
            annotation.moderation_log[0].old_moderation_status
            == ModerationStatus.APPROVED
        )
        assert (
            annotation.moderation_log[0].new_moderation_status
            == ModerationStatus.DENIED
        )

    @pytest.mark.parametrize("moderation_status", [None, ModerationStatus.APPROVED])
    @pytest.mark.parametrize("shared", [False, True])
    def test_update_status_initializes_moderation_status(
        self, svc, annotation, moderation_status, shared
    ):
        annotation.moderation_status = moderation_status
        annotation.shared = shared

        svc.update_status(annotation)

        if not moderation_status and shared:
            assert annotation.moderation_status == ModerationStatus.APPROVED
        else:
            assert annotation.moderation_status == moderation_status

    @pytest.fixture(autouse=True)
    def moderated_annotations(self, factories):
        return factories.Annotation.create_batch(
            3, moderation_status=ModerationStatus.DENIED
        )

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def user(self, factories, db_session):
        user = factories.User()
        db_session.flush()
        return user


@pytest.fixture
def svc(db_session):
    return AnnotationModerationService(db_session)


class TestAnnotationModerationServiceFactory:
    def test_it_returns_service(self, pyramid_request):
        svc = annotation_moderation_service_factory(None, pyramid_request)
        assert isinstance(svc, AnnotationModerationService)
