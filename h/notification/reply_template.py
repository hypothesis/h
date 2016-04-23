# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from pyramid import security
from pyramid.events import subscriber
from pyramid.renderers import render

from h import auth
from h.auth.util import translate_annotation_principals
from h.api import storage
from h.notification.notifier import TemplateRenderException
from h.notification import types
from h.notification.models import Subscriptions
from h.notification.gateway import user_name, \
    user_profile_url, standalone_url, get_user_by_name
from h.notification.types import ROOT_PATH, REPLY_TYPE
from h.accounts.events import LoginEvent, RegistrationEvent

log = logging.getLogger(__name__)

TXT_TEMPLATE = ROOT_PATH + 'reply_notification.txt.jinja2'
HTML_TEMPLATE = ROOT_PATH + 'reply_notification.html.jinja2'
SUBJECT_TEMPLATE = ROOT_PATH + 'reply_notification_subject.txt.jinja2'


def create_template_map(request, reply, parent):
    document_title = ''
    if reply.document:
        document_title = reply.document.title

    if document_title is '':
        document_title = parent.target_uri

    parent_user = user_name(parent.userid)
    reply_user = user_name(reply.userid)

    token = request.registry.notification_serializer.dumps({
        'type': REPLY_TYPE,
        'uri': parent.userid,
    })
    unsubscribe = request.route_url('unsubscribe', token=token)

    return {
        'document_title': document_title,
        'document_path': parent.target_uri,
        'parent_text': parent.text,
        'parent_user': parent_user,
        'parent_timestamp': format_timestamp(parent.created),
        'parent_user_profile': user_profile_url(request, parent.userid),
        'parent_path': standalone_url(request, parent.id),
        'reply_text': reply.text,
        'reply_user': reply_user,
        'reply_timestamp': format_timestamp(reply.created),
        'reply_user_profile': user_profile_url(request, reply.userid),
        'reply_path': standalone_url(request, reply.id),
        'unsubscribe': unsubscribe
    }


def format_timestamp(timestamp, now=datetime.utcnow):
    template_format = '%d %B at %H:%M'
    if timestamp.year < now().year:
        template_format = '%d %B %Y at %H:%M'
    return timestamp.strftime(template_format)


def get_recipients(request, parent):
    username = user_name(parent.userid)
    user_obj = get_user_by_name(request, username)
    if not user_obj:
        raise TemplateRenderException('User not found')
    return [user_obj.email]


def check_conditions(annotation, data):
    # Do not notify users about their own replies
    if annotation.userid == data['parent'].userid:
        return False

    # Is he the proper user?
    if data['parent'].userid != data['subscription']['uri']:
        return False

    # Else okay
    return True


def generate_notifications(request, annotation, action):
    # Only send notifications when new annotations are created
    if action != 'create':
        return

    # If the annotation doesn't have a parent, we can't find its parent, or we
    # have no idea who the author of the parent is, then we can't send a
    # notification email.
    parent_id = annotation.parent_id
    if parent_id is None:
        return
    parent = storage.fetch_annotation(request, parent_id)
    if parent is None or not annotation.userid:
        return

    # Don't send reply notifications to the author of the parent annotation if
    # the author doesn't have permission to read the reply.
    if not auth.has_permission(request, annotation, parent.userid, 'read'):
        return

    # Store the parent values as additional data
    data = {
        'parent': parent
    }

    subscriptions = Subscriptions.get_active_subscriptions_for_a_type(
        types.REPLY_TYPE)
    for subscription in subscriptions:
        data['subscription'] = subscription.__json__(request)

        # Validate annotation
        if check_conditions(annotation, data):
            try:
                subject, text, html, recipients = render_reply_notification(
                    request,
                    annotation,
                    parent)
                yield subject, text, html, recipients
            # ToDo: proper exception handling here
            except TemplateRenderException:
                log.exception('Failed to render subscription'
                              ' template %s', subscription)
            except:
                log.exception('Unknown error when trying to render'
                              ' subscription template %s', subscription)


def render_reply_notification(request, annotation, parent):
    # Render e-mail parts
    tmap = create_template_map(request, annotation, parent)
    text = render(TXT_TEMPLATE, tmap, request).strip()
    html = render(HTML_TEMPLATE, tmap, request).strip()
    subject = render(SUBJECT_TEMPLATE, tmap, request).strip()
    recipients = get_recipients(request, parent)
    return subject, text, html, recipients


# Create a reply template for a uri
def create_subscription(request, uri, active):
    subs = Subscriptions(
        uri=uri,
        type=types.REPLY_TYPE,
        active=active
    )

    request.db.add(subs)
    request.db.flush()


@subscriber(RegistrationEvent)
def registration_subscriptions(event):
    request = event.request
    user_uri = u'acct:{}@{}'.format(event.user.username, request.domain)
    create_subscription(event.request, user_uri, True)


# For backwards compatibility, generate reply notification if not exists
@subscriber(LoginEvent)
def check_reply_subscriptions(event):
    request = event.request
    user_uri = 'acct:{}@{}'.format(event.user.username, request.domain)
    res = Subscriptions.get_templates_for_uri_and_type(user_uri,
                                                       types.REPLY_TYPE)
    if not len(res):
        create_subscription(event.request, user_uri, True)


def includeme(config):
    config.scan(__name__)
