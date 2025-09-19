from dataclasses import asdict

from h_pyramid_sentry import report_exception
from kombu.exceptions import OperationalError
from pyramid.renderers import render

from h import links
from h.events import AnnotationAction
from h.models import Annotation, ModerationLog, ModerationStatus, Subscriptions, User
from h.services.email import EmailData, EmailTag, TaskData
from h.services.subscription import SubscriptionService
from h.services.user import UserService
from h.tasks import email


class AnnotationModerationService:
    def __init__(
        self,
        session,
        user_service: UserService,
        subscription_service: SubscriptionService,
        email_subaccount: str | None = None,
    ):
        self._session = session
        self._user_service = user_service
        self._subscription_service = subscription_service
        self._email_subaccount = email_subaccount

    def all_hidden(self, annotation_ids: str) -> set[str]:
        """
        Check which of the given annotation ids is hidden.

        :param annotation_ids: The ids of the annotations to check.
        :returns: The subset of the annotation ids that are hidden.
        """
        if not annotation_ids:
            return set()

        query = self._session.query(Annotation).filter(
            Annotation.id.in_(annotation_ids)
        )
        return {a.id for a in query if a.is_hidden}

    def set_status(
        self,
        annotation: Annotation,
        status: ModerationStatus | None,
        user: User | None = None,
    ) -> ModerationLog | None:
        """Set the moderation status for an annotation."""
        if status and status != annotation.moderation_status:
            moderation_log = ModerationLog(
                annotation=annotation,
                old_moderation_status=annotation.moderation_status,
                new_moderation_status=status,
                moderator=user,
            )

            self._session.add(moderation_log)
            annotation.moderation_status = status
            if annotation.slim:
                # We only have to worry about AnnotationSlim if we already have one
                # if we don't the process to create it will set the right value here
                annotation.slim.moderated = annotation.is_hidden

            return moderation_log

        return None

    def update_status(self, action: AnnotationAction, annotation: Annotation) -> None:
        """Change the moderation status of an annotation based on the action taken."""
        new_status = None

        if not annotation.moderation_status and annotation.shared:
            # If an annotation is not private but doesn't have a moderation status
            # it means that the moderation status hasn't been migrated yet.
            # Set the default `APPROVED` status
            if action == "update":
                # If the annotation was updated we want to record this in the moderation log
                self.set_status(annotation, ModerationStatus.APPROVED)
            else:
                annotation.moderation_status = ModerationStatus.APPROVED

        if not annotation.shared:
            return

        pre_moderated = annotation.group.pre_moderated
        if action == "create":
            if pre_moderated:
                new_status = ModerationStatus.PENDING
            else:
                new_status = ModerationStatus.APPROVED
        elif action == "update":
            if (
                pre_moderated
                and annotation.moderation_status == ModerationStatus.APPROVED
            ):
                new_status = ModerationStatus.PENDING

            if annotation.moderation_status == ModerationStatus.DENIED:
                new_status = ModerationStatus.PENDING

        self.set_status(annotation, new_status)

    def queue_moderation_change_email(self, request, moderation_log_id: int) -> None:
        """Queue an email to be sent to the user about moderation changes on their annotations."""

        moderation_log = self._session.get(ModerationLog, moderation_log_id)

        annotation = moderation_log.annotation
        group = annotation.group
        author = self._user_service.fetch(annotation.userid)

        if not group.pre_moderated:
            # We'll start only sending these emails for pre-moderated groups
            # For now this ties these emails to the FF for moderation emails
            return

        if not author or not author.email:
            # We can't email the user if we don't have an email for them.
            return

        # If there is no active 'moderation' subscription for the user being mentioned.
        if not self._subscription_service.get_subscription(
            user_id=author.userid, type_=Subscriptions.Type.MODERATION
        ).active:
            return

        old_status = moderation_log.old_moderation_status
        new_status = moderation_log.new_moderation_status

        # These are the transitions that will trigger an email to be sent
        email_sending_status_changes = {
            (ModerationStatus.PENDING, ModerationStatus.APPROVED),
            (ModerationStatus.PENDING, ModerationStatus.DENIED),
            (ModerationStatus.APPROVED, ModerationStatus.PENDING),
            (ModerationStatus.APPROVED, ModerationStatus.DENIED),
            (ModerationStatus.DENIED, ModerationStatus.APPROVED),
            (ModerationStatus.SPAM, ModerationStatus.APPROVED),
        }
        if (old_status, new_status) not in email_sending_status_changes:
            return

        template_base = "h:templates/emails/annotation_moderation_notification"
        context = {
            "user_display_name": author.display_name or f"@{author.username}",
            "annotation_url": links.incontext_link(request, annotation)
            or request.route_url("annotation", id=annotation.id),
            "annotation": annotation,
            "annotation_quote": annotation.quote,
            "app_url": request.registry.settings.get("h.app_url"),
            "unsubscribe_url": request.route_url(
                "unsubscribe",
                token=self._subscription_service.get_unsubscribe_token(
                    user_id=author.userid, type_=Subscriptions.Type.MODERATION
                ),
            ),
            "preferences_url": request.route_url("account_notifications"),
            "status_change_description": self.email_status_change_description(
                group.name, new_status
            ),
        }
        email_data = EmailData(
            recipients=[author.email],
            subject=self.email_subject(group.name, new_status),
            body=render(f"{template_base}.txt.jinja2", context, request=request),
            html=render(f"{template_base}.html.jinja2", context, request=request),
            tag=EmailTag.MODERATION,
            subaccount=self._email_subaccount,
            reply_to=group.reply_to,
            from_name=group.email_from_name,
        )
        task_data = TaskData(
            tag=email_data.tag,
            sender_id=author.id,
            recipient_ids=[author.id],
            extra={"annotation_id": annotation.id},
        )
        try:
            email.send.delay(asdict(email_data), asdict(task_data))
        except OperationalError as err:  # pragma: no cover
            report_exception(err)

    @staticmethod
    def email_subject(group_name: str, new_status: ModerationStatus) -> str:
        """Generate the email subject based on the moderation status change."""
        if new_status == ModerationStatus.DENIED:
            return f"Your comment in {group_name} has been declined"

        if new_status == ModerationStatus.APPROVED:
            return f"Your comment in {group_name} has been approved"

        if new_status == ModerationStatus.PENDING:
            return f"Your comment in {group_name} is pending approval"

        msg = f"Unexpected moderation status change to {new_status}"  # pragma: no cover
        raise ValueError(msg)

    @staticmethod
    def email_status_change_description(
        group_name: str, new_status: ModerationStatus
    ) -> str:
        if new_status == ModerationStatus.DENIED:
            return (
                f"The following comment has been declined by the moderation team for {group_name}.\n"
                "You can edit this comment and it will be reevaluated by that group's moderators."
            )

        if new_status == ModerationStatus.PENDING:
            return (
                f"The following comment has been hidden by the moderation team for {group_name} and is only visible to that group's moderators and yourself.\n"
                "You'll receive another email when your comment's moderation status changes."
            )
        if new_status == ModerationStatus.APPROVED:
            return (
                f"The following comment has been approved by the moderation team for {group_name}.\n"
                "It's now visible to everyone viewing that group."
            )

        msg = f"Unexpected moderation status change description for {new_status}"
        raise ValueError(msg)


def annotation_moderation_service_factory(_context, request):
    return AnnotationModerationService(
        request.db,
        user_service=request.find_service(name="user"),
        subscription_service=request.find_service(SubscriptionService),
        email_subaccount=request.registry.settings.get(
            "mailchimp_user_actions_subaccount"
        ),
    )
