from pyramid.renderers import render
from pyramid.request import Request

from h import links
from h.emails.util import get_user_url
from h.models import Subscriptions
from h.notification.reply import Notification
from h.services import SubscriptionService
from h.services.email import EmailData, EmailTag


def generate(request: Request, notification: Notification) -> EmailData:
    """Generate an email for a reply notification.

    :param request: the current request
    :param notification: the reply notification data structure
    """

    unsubscribe_token = request.find_service(SubscriptionService).get_unsubscribe_token(
        user_id=notification.parent_user.userid, type_=Subscriptions.Type.REPLY
    )

    context = {
        "document_title": notification.document.title or notification.parent.target_uri,
        "document_url": notification.parent.target_uri,
        # Parent related
        "parent": notification.parent,
        "parent_user_display_name": notification.parent_user.display_name
        or notification.parent_user.username,
        "parent_user_url": get_user_url(notification.parent_user, request),
        "unsubscribe_url": request.route_url(
            "unsubscribe",
            token=unsubscribe_token,
        ),
        # Reply related
        "reply": notification.reply,
        "reply_url": links.incontext_link(request, notification.reply)
        or request.route_url("annotation", id=notification.reply.id),
        "reply_user_display_name": notification.reply_user.display_name
        or notification.reply_user.username,
        "reply_user_url": get_user_url(notification.reply_user, request),
    }

    subject = f"{context['reply_user_display_name']} has replied to your annotation"
    text = render(
        "h:templates/emails/reply_notification.txt.jinja2", context, request=request
    )
    html = render(
        "h:templates/emails/reply_notification.html.jinja2", context, request=request
    )

    return EmailData(
        recipients=[notification.parent_user.email],
        subject=subject,
        body=text,
        tag=EmailTag.REPLY_NOTIFICATION,
        html=html,
    )
