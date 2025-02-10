from pyramid.renderers import render
from pyramid.request import Request

from h import links
from h.emails.util import get_user_url
from h.notification.mention import Notification


def generate(request: Request, notification: Notification):
    context = {
        "user_url": get_user_url(notification.mentioning_user, request),
        "user_display_name": notification.mentioning_user.display_name
        or notification.mentioning_user.username,
        "annotation_url": links.incontext_link(request, notification.annotation)
        or request.route_url("annotation", id=notification.annotation.id),
        "document_title": notification.document.title
        or notification.annotation.target_uri,
        "document_url": notification.annotation.target_uri,
        "annotation": notification.annotation,
    }

    subject = f"{context['user_display_name']} has mentioned you in an annotation"
    text = render(
        "h:templates/emails/mention_notification.txt.jinja2", context, request=request
    )
    html = render(
        "h:templates/emails/mention_notification.html.jinja2", context, request=request
    )

    return [notification.mentioned_user.email], subject, text, html
