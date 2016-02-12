# -*- coding: utf-8 -*-
import logging
import re
from datetime import datetime

from pyramid.events import subscriber
from pyramid.renderers import render

from h import auth
from h.api.auth import translate_annotation_principals
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
    if 'document' in reply:
        document_title = reply['document'].get('title', '')

    if document_title is '':
        document_title = parent['uri']

    parent_user = user_name(parent['user'])
    reply_user = user_name(reply['user'])

    token = request.registry.notification_serializer.dumps({
        'type': REPLY_TYPE,
        'uri': parent['user'],
    })
    unsubscribe = request.route_url('unsubscribe', token=token)

    return {
        'document_title': document_title,
        'document_path': parent['uri'],
        'parent_text': parent.get('text', ''),
        'parent_user': parent_user,
        'parent_timestamp': format_timestamp(parent['created']),
        'parent_user_profile': user_profile_url(request, parent['user']),
        'parent_path': standalone_url(request, parent['id']),
        'reply_text': reply['text'],
        'reply_user': reply_user,
        'reply_timestamp': format_timestamp(reply['created']),
        'reply_user_profile': user_profile_url(request, reply['user']),
        'reply_path': standalone_url(request, reply['id']),
        'unsubscribe': unsubscribe
    }


def format_timestamp(timestamp):
    # Currently we cut the UTC format because time.strptime has problems
    # parsing it, and of course it'd only correct the backend's timezone
    # which is not meaningful for international users. This trims the
    # timezone in the format +00:00.
    timestamp = re.sub(r'\+\d\d:\d\d$', '', timestamp)
    timestamp_format = '%Y-%m-%dT%H:%M:%S.%f'
    parsed = datetime.strptime(timestamp, timestamp_format)

    template_format = '%d %B at %H:%M'
    if parsed.year < datetime.now().year:
        template_format = '%d %B %Y at %H:%M'
    return parsed.strftime(template_format)


def get_recipients(request, parent):
    username = user_name(parent['user'])
    user_obj = get_user_by_name(request, username)
    if not user_obj:
        raise TemplateRenderException('User not found')
    return [user_obj.email]


def check_conditions(annotation, data):
    # Do not notify users about their own replies
    if annotation['user'] == data['parent']['user']:
        return False

    # Is he the proper user?
    if data['parent']['user'] != data['subscription']['uri']:
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
    parent = storage.fetch_annotation(annotation.parent_id)
    if parent is None or 'user' not in parent:
        return

    # We don't send replies to the author of the parent unless they're going to
    # be able to read it. That means there must be some overlap between the set
    # of effective principals of the parent's author, and the read permissions
    # of the reply.
    child_read_permissions = annotation.get('permissions', {}).get('read', [])
    parent_principals = auth.effective_principals(parent['user'], request)
    read_principals = translate_annotation_principals(child_read_permissions)
    if not set(parent_principals).intersection(read_principals):
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
    user_uri = 'acct:{}@{}'.format(event.user.username, request.domain)
    create_subscription(event.request, user_uri, True)
    event.user.subscriptions = True


# For backwards compatibility, generate reply notification if not exists
@subscriber(LoginEvent)
def check_reply_subscriptions(event):
    request = event.request
    user_uri = 'acct:{}@{}'.format(event.user.username, request.domain)
    res = Subscriptions.get_templates_for_uri_and_type(user_uri,
                                                       types.REPLY_TYPE)
    if not len(res):
        create_subscription(event.request, user_uri, True)
        event.user.subscriptions = True


def includeme(config):
    config.scan(__name__)
