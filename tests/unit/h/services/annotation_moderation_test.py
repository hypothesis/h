from unittest.mock import Mock, sentinel

import pytest

from h.models.annotation import ModerationStatus
from h.models.notification import EmailTag
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

    def test_queue_moderation_change_email_when_group_not_pre_moderated(
        self, svc, factories, email, pyramid_request
    ):
        group = factories.Group(pre_moderated=False)
        annotation = factories.Annotation(group=group)
        moderation_log = factories.ModerationLog(annotation=annotation)

        svc.queue_moderation_change_email(pyramid_request, moderation_log.id)

        email.send.delay.assert_not_called()

    def test_queue_moderation_change_email_when_no_email(
        self,
        svc,
        factories,
        email,
        pyramid_request,
        user_service,
    ):
        user_service.fetch.return_value = factories.User(email=None)
        group = factories.Group(pre_moderated=True)
        annotation = factories.Annotation(group=group)
        moderation_log = factories.ModerationLog(annotation=annotation)

        svc.queue_moderation_change_email(pyramid_request, moderation_log.id)

        email.send.delay.assert_not_called()

    def test_queue_moderation_change_email_when_no_subscription(
        self,
        svc,
        factories,
        email,
        pyramid_request,
        subscription_service,
    ):
        subscription_service.get_subscription.return_value = Mock(active=False)
        group = factories.Group(pre_moderated=True)
        annotation = factories.Annotation(group=group)
        moderation_log = factories.ModerationLog(annotation=annotation)

        svc.queue_moderation_change_email(pyramid_request, moderation_log.id)

        email.send.delay.assert_not_called()

    def test_queue_moderation_change_email_for_status_that_dont_trigger_emails(
        self, svc, factories, email, pyramid_request
    ):
        group = factories.Group(pre_moderated=True)
        annotation = factories.Annotation(group=group)
        moderation_log = factories.ModerationLog(
            annotation=annotation, new_moderation_status=ModerationStatus.SPAM
        )

        svc.queue_moderation_change_email(pyramid_request, moderation_log.id)

        email.send.delay.assert_not_called()

    def test_queue_moderation_change_email_sent(
        self,
        svc,
        factories,
        email,
        pyramid_request,
        user_service,
        html_renderer,
        text_renderer,
        subscription_service,
    ):
        user = factories.User()
        user_service.fetch.return_value = user
        group = factories.Group(pre_moderated=True, name="GROUP NAME")
        annotation = factories.Annotation(group=group)
        moderation_log = factories.ModerationLog(
            annotation=annotation,
            old_moderation_status=ModerationStatus.PENDING,
            new_moderation_status=ModerationStatus.APPROVED,
        )

        svc.queue_moderation_change_email(pyramid_request, moderation_log.id)

        expected_context = {
            "user_display_name": user.display_name,
            "annotation_url": pyramid_request.route_url("annotation", id=annotation.id),
            "annotation": annotation,
            "annotation_quote": annotation.quote,
            "unsubscribe_url": pyramid_request.route_url(
                "unsubscribe",
                token=subscription_service.get_unsubscribe_token.return_value,
            ),
            "status_change_description": "The following comment has been approved by the moderation team for GROUP NAME.\nIt's now visible to everyone viewing that group.",
        }
        html_renderer.assert_(**expected_context)  # noqa: PT009
        text_renderer.assert_(**expected_context)  # noqa: PT009
        email.send.delay.assert_called_once_with(
            {
                "recipients": [user.email],
                "subject": "Your comment in GROUP NAME has been approved",
                "body": "",
                "tag": EmailTag.MODERATION,
                "html": "",
                "subaccount": sentinel.email_subaccount,
                "reply_to": None,
            },
            {
                "tag": EmailTag.MODERATION,
                "sender_id": user.id,
                "recipient_ids": [user.id],
                "extra": {"annotation_id": annotation.id},
            },
        )

    @pytest.mark.parametrize(
        "new_status,subject",
        [
            (ModerationStatus.APPROVED, "Your comment in GROUP NAME has been approved"),
            (
                ModerationStatus.PENDING,
                "Your comment in GROUP NAME is pending approval",
            ),
            (ModerationStatus.DENIED, "Your comment in GROUP NAME has been declined"),
        ],
    )
    def test_email_subject(self, new_status, subject, svc, factories):
        group = factories.Group(name="GROUP NAME")
        assert svc.email_subject(group.name, new_status) == subject

    def test_email_subject_raises_value_error_for_unexpected_status(self, svc):
        with pytest.raises(ValueError, match="Unexpected moderation status"):
            svc.email_subject("GROUP NAME", ModerationStatus.SPAM)

    @pytest.mark.parametrize(
        "new_status,description",
        [
            (
                ModerationStatus.APPROVED,
                "The following comment has been approved by the moderation team for GROUP NAME.\nIt's now visible to everyone viewing that group.",
            ),
            (
                ModerationStatus.PENDING,
                "The following comment has been hidden by the moderation team for GROUP NAME and is only visible to that group's moderators and yourself.\nYou'll receive another email when your comment's moderation status changes.",
            ),
            (
                ModerationStatus.DENIED,
                "The following comment has been declined by the moderation team for GROUP NAME.\n"
                "You can edit this comment and it will be reevaluated by that group's moderators.",
            ),
        ],
    )
    def test_email_description(self, new_status, description, svc, factories):
        group = factories.Group(name="GROUP NAME")
        assert (
            svc.email_status_change_description(group.name, new_status) == description
        )

    def test_email_description_raises_value_error_for_unexpected_status(self, svc):
        with pytest.raises(ValueError, match="Unexpected moderation status"):
            svc.email_status_change_description("GROUP NAME", ModerationStatus.SPAM)

    @pytest.fixture
    def email(self, patch):
        return patch("h.services.annotation_moderation.email")

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

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("annotation", "/ann/{id}")
        pyramid_config.add_route("unsubscribe", "/unsub/{token}")
        pyramid_config.add_route(
            "account_notifications", "/account/settings/notifications"
        )

    @pytest.fixture(autouse=True)
    def html_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/annotation_moderation_notification.html.jinja2"
        )

    @pytest.fixture(autouse=True)
    def text_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer(
            "h:templates/emails/annotation_moderation_notification.txt.jinja2"
        )


@pytest.fixture
def svc(db_session, user_service, subscription_service):
    return AnnotationModerationService(
        db_session,
        user_service=user_service,
        subscription_service=subscription_service,
        email_subaccount=sentinel.email_subaccount,
    )


class TestAnnotationModerationServiceFactory:
    @pytest.mark.usefixtures("user_service", "subscription_service")
    def test_it_returns_service(self, pyramid_request):
        svc = annotation_moderation_service_factory(None, pyramid_request)
        assert isinstance(svc, AnnotationModerationService)
