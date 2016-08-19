# -*- coding: utf-8 -*-

from h import links

from pyramid.renderers import render


def generate(request, notification):
    """
    Generate an email for a reply notification.

    :param request: the current request
    :type request: pyramid.request.Request
    :param notification: the reply notification data structure
    :type notification: h.notifications.reply.Notification

    :returns: a 4-element tuple containing: recipients, subject, text, html
    """
    document_title = notification.document.title
    if not document_title:
        document_title = notification.parent.target_uri

    parent_user_url = request.route_url('stream.user_query',
                                        user=notification.parent_user.username)

    reply_url = links.incontext_link(request, notification.reply)
    if not reply_url:
        reply_url = request.route_url('annotation', id=notification.reply.id)

    reply_user_url = request.route_url('stream.user_query',
                                       user=notification.reply_user.username)

    unsubscribe_token = _unsubscribe_token(request, notification.parent_user)
    unsubscribe_url = request.route_url('unsubscribe', token=unsubscribe_token)

    context = {
        'document_title': document_title,
        'document_url': notification.parent.target_uri,
        'parent': notification.parent,
        'parent_user': notification.parent_user,
        'parent_user_url': parent_user_url,
        'reply': notification.reply,
        'reply_url': reply_url,
        'reply_user': notification.reply_user,
        'reply_user_url': reply_user_url,
        'unsubscribe_url': unsubscribe_url,
    }

    subject = '{user} has replied to your annotation'.format(
        user=notification.reply_user.username)
    text = render('h:templates/emails/reply_notification.txt.jinja2',
                  context,
                  request=request)
    html = render('h:templates/emails/reply_notification.html.jinja2',
                  context,
                  request=request)

    return [notification.parent_user.email], subject, text, html


def _unsubscribe_token(request, user):
    serializer = request.registry.notification_serializer
    return serializer.dumps({'type': 'reply', 'uri': user.userid})
