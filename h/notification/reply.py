import logging
from collections import namedtuple

from h import storage
from h.models import Subscriptions
from h.services import SubscriptionService

log = logging.getLogger(__name__)


class Notification(
    namedtuple(
        "Notification", ["reply", "reply_user", "parent", "parent_user", "document"]
    )
):
    """
    A data structure representing a notification of a reply to an annotation.

    :param reply: the reply annotation
    :type reply: h.models.Annotation
    :param reply_user: the user who made the reply annotation
    :type reply_user: h.models.User
    :param parent: the annotation being replied to
    :type parent: h.models.Annotation
    :param parent_user: the user being replied to
    :type parent_user: h.models.User
    :param document: the document for the page on which the reply happened
    :type document: h.models.Document
    """


def get_notification(
    request, annotation, action
):  # pylint: disable=too-many-return-statements,too-complex
    """
    Check if the passed annotation and action pair should send a notification.

    Checks to see if the annotation event represented by the passed annotation
    and action should trigger a notification. If it should, this function
    returns the relevant :py:class:`~h.notification.reply.Notification` object.
    Otherwise, it returns None.

    :param request: the current request object
    :type request: pyramid.request.Request
    :param annotation: the reply annotation
    :type annotation: h.models.Annotation
    :param action: the event action
    :type action: str

    :returns: a :py:class:`~h.notification.reply.Notification`, or None
    """
    # Only send notifications when new annotations are created
    if action != "create":
        return None

    # If the annotation doesn't have a parent, or we can't find its parent,
    # then we can't send a notification email.
    parent_id = annotation.parent_id
    if parent_id is None:
        return None

    # Now we know we're dealing with a reply
    reply = annotation

    parent = storage.fetch_annotation(request.db, parent_id)
    if parent is None:
        return None

    user_service = request.find_service(name="user")

    # If the parent user doesn't exist (anymore), we can't send an email.
    parent_user = user_service.fetch(parent.userid)
    if parent_user is None:
        return None

    # If the parent user doesn't have an email address we can't email them.
    if not parent_user.email:
        return None

    # If the reply user doesn't exist (anymore), we can't send an email, but
    # this would be super weird, so log a warning.
    reply_user = user_service.fetch(reply.userid)
    if reply_user is None:
        log.warning("user who just replied no longer exists: %s", reply.userid)
        return None

    # Do not notify users about their own replies
    if parent_user == reply_user:
        return None

    # Don't send reply notifications to the author of the parent annotation if
    # the reply was private.
    if not reply.shared:
        return None

    # FIXME: we should be retrieving the document from the root annotation, not
    # the reply, and dealing with the possibility that we have no document
    # metadata.
    if reply.document is None:
        return None

    # Bail if there is no active 'reply' subscription for the user being
    # replied to.
    if (
        not request.find_service(SubscriptionService)
        .get_subscription(user_id=parent.userid, type_=Subscriptions.Type.REPLY)
        .active
    ):
        return None

    return Notification(reply, reply_user, parent, parent_user, reply.document)


def includeme(config):
    config.scan(__name__)
