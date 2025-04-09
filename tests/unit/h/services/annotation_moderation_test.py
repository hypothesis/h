import pytest

from h.models.annotation import ModerationStatus
from h.services.annotation_moderation import (
    AnnotationModerationService,
    annotation_moderation_service_factory,
)


class TestModerationStatusService:
    def test_all_hidden_lists_moderated_annotation_ids(self, svc, mods):
        ids = [m.annotation.id for m in mods[0:-1]]
        assert svc.all_hidden(ids) == set(ids)

    def test_all_hidden_skips_non_moderated_annotations(self, svc, factories):
        annotation = factories.Annotation()

        assert svc.all_hidden([annotation.id]) == set()

    def test_all_hidden_handles_with_no_ids(self, svc):
        assert svc.all_hidden([]) == set()

    # fmt: off
    @pytest.mark.parametrize("action,is_private,pre_moderation_enabled,existing_status,expected_status", [
        #When a new annotation is created:
        #If the group has pre-moderation disabled the annotation's initial moderation state should be Approved.
        #If the group has pre-moderation enabled the annotation's initial moderation state should be Pending.
        ("created", False, False, None, ModerationStatus.APPROVED),
        ("created", False, True, None, ModerationStatus.PENDING),
        #When an Approved annotation is edited:
        #If the group has pre-moderation disabled the moderation state doesn't change
        #If the group has pre-moderation enabled the moderation state changes to Pending
        ("updated", False, False, ModerationStatus.APPROVED, ModerationStatus.APPROVED),
        ("updated", False, False, ModerationStatus.DENIED, ModerationStatus.DENIED),
        ("updated", False, True, ModerationStatus.APPROVED, ModerationStatus.PENDING),
        #When a Denied annotation is edited the moderation state changes to Pending
        #(whether pre-moderation is disabled or enabled)
        ("updated", False, True, ModerationStatus.DENIED, ModerationStatus.PENDING),
        ("updated", False, False, ModerationStatus.DENIED, ModerationStatus.PENDING),
        #When a Pending annotation is edited its moderation state doesn't change
        #(whether pre-moderation is disabled or enabled)
        ("updated", False, False, ModerationStatus.PENDING, ModerationStatus.PENDING),
        ("updated", False, True, ModerationStatus.PENDING, ModerationStatus.PENDING),
        #When a Spam annotation is edited its moderation state doesn't change
        #(whether pre-moderation is disabled or enabled)
        ("updated", False, False, ModerationStatus.SPAM, ModerationStatus.SPAM),
        ("updated", False, True, ModerationStatus.SPAM, ModerationStatus.SPAM),
        #Editing a private annotation does not change its moderation state as long as the annotation remains private:
        #A private annotation whose state is NULL will remain NULL if edited.
        ("updated", True, False, None, None),
        #A private annotation whose state is Pending will remain Pending if edited.
        ("updated", True, False, ModerationStatus.PENDING, ModerationStatus.PENDING),
        #A private annotation whose state is Approved will remain Approved if edited.
        ("updated", True, False, ModerationStatus.APPROVED, ModerationStatus.APPROVED),
        #A private annotation whose state is Denied will remain Denied if edited.
        ("updated", True,False, ModerationStatus.DENIED, ModerationStatus.DENIED),
        #A private annotation whose state is Spam will remain Spam if edited.
        ("updated", True, False, ModerationStatus.SPAM, ModerationStatus.SPAM),
        # When a new private annotation is created the annotation's initial moderation state should be NULL.
        # This is the same whether pre-moderation is enabled or disabled.
        # It should not be possible for a shared annotation to have the NULL state.
        ("created", True, False, None, None),
        ("created", True, True, None, None),
        # It should not be possible for a shared annotation to have the NULL state.
        # We are not migrating all null and shared annotations to approved so this can happen.
        # We could write an XFAIL test here
    ])
    # fmt: on
    def test_update_status(self, svc, action, is_private, pre_moderation_enabled, existing_status, expected_status, factories):
        group = factories.Group(pre_moderated=pre_moderation_enabled)
        annotation = factories.Annotation(moderation_status=existing_status, shared=not is_private)

        svc.update_status(action, annotation, group)

        assert annotation.moderation_status== expected_status

    @pytest.fixture(autouse=True)
    def mods(self, factories):
        return factories.AnnotationModeration.create_batch(3)

    @pytest.fixture
    def svc(self, db_session):
        return AnnotationModerationService(db_session)


class TestModerationStatusServiceFactory:
    def test_it_returns_service(self, pyramid_request):
        svc = annotation_moderation_service_factory(None, pyramid_request)
        assert isinstance(svc, AnnotationModerationService)
