import logging
from dataclasses import dataclass

from h.models import Annotation, Document, Subscriptions, User
from h.services import SubscriptionService

logger = logging.getLogger(__name__)


@dataclass
class MentionNotification:
    """A data structure representing a mention notification in an annotation."""

    mentioning_user: User
    mentioned_user: User
    annotation: Annotation
    document: Document


def get_notifications(
    request, annotation: Annotation, action
) -> list[MentionNotification]:
    # Only send notifications when annotations are created or updated
    if action not in {"create", "update"}:
        return []

    # Only send notifications for shared annotations
    if not annotation.shared:
        return []

    user_service = request.find_service(name="user")

    # If the mentioning user doesn't exist (anymore), we can't send emails, but
    # this would be super weird, so log a warning.
    mentioning_user = user_service.fetch(annotation.userid)
    if mentioning_user is None:
        logger.warning(
            "user who just mentioned another user no longer exists: %s",
            annotation.userid,
        )
        return []

    subscription_service = request.find_service(SubscriptionService)

    notifications = []
    for mention in annotation.mentions:
        # If the mentioned user doesn't exist (anymore), we can't send emails
        mentioned_user = user_service.fetch(mention.user.userid)
        if mentioned_user is None:
            continue

        # If mentioned user doesn't have an email address we can't email them.
        if not mention.user.email:
            continue

        # If the mentioning user mentions self, we don't want to send an email.
        if mentioned_user == mentioning_user:
            continue

        # If the annotation doesn't have a document, we can't send an email.
        if annotation.document is None:
            continue

        # Bail if there is no active 'mention' subscription for the user being mentioned.
        if not subscription_service.get_subscription(
            user_id=mentioned_user.userid, type_=Subscriptions.Type.MENTION
        ).active:
            continue

        notifications.append(
            MentionNotification(
                mentioning_user, mentioned_user, annotation, annotation.document
            )
        )

    return notifications
