from pyramid.renderers import render
from pyramid.request import Request

from h import links
from h.models import Subscriptions
from h.notification.mention import MentionNotification
from h.services import SubscriptionService
from h.services.email import EmailData, EmailTag


def generate(request: Request, notification: MentionNotification) -> EmailData:
    username = notification.mentioning_user.username

    unsubscribe_token = request.find_service(SubscriptionService).get_unsubscribe_token(
        user_id=notification.mentioned_user.userid, type_=Subscriptions.Type.MENTION
    )

    context = {
        "username": username,
        "user_display_name": notification.mentioning_user.display_name
        or f"@{username}",
        "annotation_url": links.incontext_link(request, notification.annotation)
        or request.route_url("annotation", id=notification.annotation.id),
        "document_title": notification.document.title
        or notification.annotation.target_uri,
        "document_url": notification.annotation.target_uri,
        "annotation": notification.annotation,
        "annotation_quote": notification.annotation.quote,
        "app_url": request.registry.settings.get("h.app_url"),
        "unsubscribe_url": request.route_url(
            "unsubscribe",
            token=unsubscribe_token,
        ),
        "preferences_url": request.route_url("account_notifications"),
    }

    subject = f"{context['user_display_name']} has mentioned you in an annotation"
    text = render(
        "h:templates/emails/mention_notification.txt.jinja2", context, request=request
    )
    html = render(
        "h:templates/emails/mention_notification.html.jinja2", context, request=request
    )

    return EmailData(
        recipients=[notification.mentioned_user.email],
        subject=subject,
        body=text,
        tag=EmailTag.MENTION_NOTIFICATION,
        html=html,
    )
