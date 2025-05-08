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

        svc.set_status(annotation, None, user)

        assert annotation.moderation_status is ModerationStatus.APPROVED

    def test_set_status_with_same_status_doesnt_change_it(self, svc, annotation, user):
        annotation.moderation_status = ModerationStatus.APPROVED

        svc.set_status(annotation, ModerationStatus.APPROVED, user)

        assert annotation.moderation_status is ModerationStatus.APPROVED
        assert annotation.moderation_log == []

    @pytest.mark.parametrize("with_slim", [False, True])
    def test_set_status(self, svc, annotation, user, factories, with_slim):
        annotation.moderation_status = ModerationStatus.APPROVED
        if with_slim:
            annotation.slim = factories.AnnotationSlim()

        svc.set_status(annotation, ModerationStatus.DENIED, user)

        assert annotation.moderation_status is ModerationStatus.DENIED
        assert annotation.moderation_log[0].annotation_id == annotation.id
        assert annotation.moderation_log[0].moderator_id == user.id
        assert (
            annotation.moderation_log[0].old_moderation_status
            == ModerationStatus.APPROVED
        )
        assert (
            annotation.moderation_log[0].new_moderation_status
            == ModerationStatus.DENIED
        )
        if with_slim:
            assert annotation.slim.moderated == annotation.is_hidden

    @pytest.mark.parametrize("moderation_status", [None, ModerationStatus.APPROVED])
    @pytest.mark.parametrize("shared", [False, True])
    @pytest.mark.parametrize("action", ["create", "update"])
    def test_update_status_initializes_moderation_status(
        self, svc, annotation, moderation_status, shared, action
    ):
        annotation.moderation_status = moderation_status
        annotation.shared = shared

        svc.update_status(action, annotation)

        if not moderation_status and shared:
            assert annotation.moderation_status == ModerationStatus.APPROVED
            if action == "create":
                assert not annotation.moderation_log
            else:
                assert annotation.moderation_log
        else:
            assert annotation.moderation_status == moderation_status

    @pytest.mark.parametrize(
        "action,is_private,pre_moderation_enabled,existing_status,expected_status",
        [
            # When a new annotation is created:
            # If the group has pre-moderation disabled the annotation's initial moderation state should be Approved.
            ("create", False, False, None, ModerationStatus.APPROVED),
            # If the group has pre-moderation enabled the annotation's initial moderation state should be Pending.
            ("create", False, True, None, ModerationStatus.PENDING),
            # When an Approved annotation is edited:
            # If the group has pre-moderation disabled the moderation state doesn't change
            (
                "update",
                False,
                False,
                ModerationStatus.APPROVED,
                ModerationStatus.APPROVED,
            ),
            # If the group has pre-moderation enabled the moderation state changes to Pending
            (
                "update",
                False,
                True,
                ModerationStatus.APPROVED,
                ModerationStatus.PENDING,
            ),
            # When a Denied annotation is edited the moderation state changes to Pending
            # (whether pre-moderation is disabled or enabled)
            ("update", False, True, ModerationStatus.DENIED, ModerationStatus.PENDING),
            (
                "update",
                False,
                False,
                ModerationStatus.DENIED,
                ModerationStatus.PENDING,
            ),
            # When a Pending annotation is edited its moderation state doesn't change
            # (whether pre-moderation is disabled or enabled)
            (
                "update",
                False,
                False,
                ModerationStatus.PENDING,
                ModerationStatus.PENDING,
            ),
            (
                "update",
                False,
                True,
                ModerationStatus.PENDING,
                ModerationStatus.PENDING,
            ),
            # When a Spam annotation is edited its moderation state doesn't change
            # (whether pre-moderation is disabled or enabled)
            ("update", False, False, ModerationStatus.SPAM, ModerationStatus.SPAM),
            ("update", False, True, ModerationStatus.SPAM, ModerationStatus.SPAM),
            # When a new private annotation is created the annotation's initial moderation state should be NULL.
            # This is the same whether pre-moderation is enabled or disabled.
            ("create", True, False, None, None),
            ("create", True, True, None, None),
            # Editing a private annotation does not change its moderation state as long as the annotation remains private:
            # A private annotation whose state is NULL will remain NULL if edited.
            ("update", True, False, None, None),
            # A private annotation whose state is Pending will remain Pending if edited.
            (
                "update",
                True,
                False,
                ModerationStatus.PENDING,
                ModerationStatus.PENDING,
            ),
            # A private annotation whose state is Approved will remain Approved if edited.
            (
                "update",
                True,
                False,
                ModerationStatus.APPROVED,
                ModerationStatus.APPROVED,
            ),
            # A private annotation whose state is Denied will remain Denied if edited.
            ("update", True, False, ModerationStatus.DENIED, ModerationStatus.DENIED),
            # A private annotation whose state is Spam will remain Spam if edited.
            ("update", True, False, ModerationStatus.SPAM, ModerationStatus.SPAM),
            # We don't change the moderation status of annotations when they are deleted
            ("delete", False, False, ModerationStatus.SPAM, ModerationStatus.SPAM),
        ],
    )
    def test_update_status(
        self,
        svc,
        action,
        is_private,
        pre_moderation_enabled,
        existing_status,
        expected_status,
        factories,
    ):
        group = factories.Group(pre_moderated=pre_moderation_enabled)
        annotation = factories.Annotation(
            moderation_status=existing_status, shared=not is_private, group=group
        )

        svc.update_status(action, annotation)

        assert annotation.moderation_status == expected_status

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
