from pyramid.renderers import render
from pyramid.request import Request

from h import links
from h.notification.mention import MentionNotification
from h.services.email import EmailTag


def generate(request: Request, notification: MentionNotification):
    selectors = notification.annotation.target[0].get("selector", [])
    quote = next((s for s in selectors if s.get("type") == "TextQuoteSelector"), None)
    username = notification.mentioning_user.username
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
        "annotation_quote": quote.get("exact") if quote else None,
    }

    subject = f"{context['user_display_name']} has mentioned you in an annotation"
    text = render(
        "h:templates/emails/mention_notification.txt.jinja2", context, request=request
    )
    html = render(
        "h:templates/emails/mention_notification.html.jinja2", context, request=request
    )

    return (
        [notification.mentioned_user.email],
        subject,
        text,
        EmailTag.MENTION_NOTIFICATION,
        html,
    )
