from pyramid.renderers import render

from h import links


def generate(request, notification):
    """
    Generate an email for a reply notification.

    :param request: the current request
    :type request: pyramid.request.Request
    :param notification: the reply notification data structure
    :type notification: h.notifications.reply.Notification

    :returns: a 4-element tuple containing: recipients, subject, text, html
    """

    context = {
        "document_title": notification.document.title or notification.parent.target_uri,
        "document_url": notification.parent.target_uri,
        # Parent related
        "parent": notification.parent,
        "parent_user_display_name": notification.parent_user.display_name
        or notification.parent_user.username,
        "parent_user_url": _get_user_url(notification.parent_user, request),
        "unsubscribe_url": request.route_url(
            "unsubscribe",
            token=_unsubscribe_token(request, notification.parent_user),
        ),
        # Reply related
        "reply": notification.reply,
        "reply_url": links.incontext_link(request, notification.reply)
        or request.route_url("annotation", id=notification.reply.id),
        "reply_user_display_name": notification.reply_user.display_name
        or notification.reply_user.username,
        "reply_user_url": _get_user_url(notification.reply_user, request),
    }

    subject = f"{context['reply_user_display_name']} has replied to your annotation"
    text = render(
        "h:templates/emails/reply_notification.txt.jinja2", context, request=request
    )
    html = render(
        "h:templates/emails/reply_notification.html.jinja2", context, request=request
    )

    return [notification.parent_user.email], subject, text, html


def _get_user_url(user, request):
    if user.authority == request.default_authority:
        return request.route_url("stream.user_query", user=user.username)

    return None


def _unsubscribe_token(request, user):
    serializer = request.registry.notification_serializer
    return serializer.dumps({"type": "reply", "uri": user.userid})
