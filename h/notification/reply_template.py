# -*- coding: utf-8 -*-
import logging
import re
from datetime import datetime

from pyramid.events import subscriber
from pyramid.security import Everyone, principals_allowed_by_permission
from pyramid.renderers import render
from hem.db import get_session
from horus.events import NewRegistrationEvent


from h.notification.notifier import send_email, TemplateRenderException
from h.notification import types
from h.notification.models import Subscriptions
from h.notification.gateway import user_name, \
    user_profile_url, standalone_url, get_user_by_name
from h.notification.types import ROOT_PATH, REPLY_TYPE
from h.accounts.events import LoginEvent
from h.events import AnnotationEvent
from h.models import Annotation

log = logging.getLogger(__name__)

TXT_TEMPLATE = ROOT_PATH + 'reply_notification.txt'
HTML_TEMPLATE = ROOT_PATH + 'reply_notification.html'
SUBJECT_TEMPLATE = ROOT_PATH + 'reply_notification_subject.txt'


def parent_values(annotation):
    if 'references' in annotation:
        parent = Annotation.fetch(annotation['references'][-1])
        if 'references' in parent:
            grandparent = Annotation.fetch(parent['references'][-1])
            parent['quote'] = grandparent['text']
        return parent
    else:
        return {}


def create_template_map(request, reply, data):
    document_title = ''
    if 'document' in reply:
        document_title = reply['document'].get('title', '')

    if document_title is '':
        document_title = data['parent']['uri']

    parent_user = user_name(data['parent']['user'])
    reply_user = user_name(reply['user'])

    token = request.registry.notification_serializer.dumps({
        'type': REPLY_TYPE,
        'uri': data['parent']['user'],
    })
    unsubscribe = request.route_url('unsubscribe', token=token)

    return {
        'document_title': document_title,
        'document_path': data['parent']['uri'],
        'parent_text': data['parent']['text'],
        'parent_user': parent_user,
        'parent_timestamp': format_timestamp(data['parent']['created']),
        'parent_user_profile': user_profile_url(
            request, data['parent']['user']),
        'parent_path': standalone_url(request, data['parent']['id']),
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


def get_recipients(request, data):
    username = user_name(data['parent']['user'])
    user_obj = get_user_by_name(request, username)
    if not user_obj:
        raise TemplateRenderException('User not found')
    return [user_obj.email]


def check_conditions(annotation, data):
    # Get the e-mail of the owner
    if 'user' not in data['parent'] or not data['parent']['user']:
        return False
    # Do not notify users about their own replies
    if annotation['user'] == data['parent']['user']:
        return False

    # Is he the proper user?
    if data['parent']['user'] != data['subscription']['uri']:
        return False

    # Else okay
    return True


@subscriber(AnnotationEvent)
def send_notifications(event):
    # Extract data
    action = event.action
    request = event.request
    annotation = event.annotation

    # And for them we need only the creation action
    if action != 'create':
        return

    # Check for authorization. Send notification only for public annotation
    # XXX: This will be changed and fine grained when
    # user groups will be introduced
    if Everyone not in principals_allowed_by_permission(annotation, 'read'):
        return

    # Store the parent values as additional data
    data = {
        'parent': parent_values(annotation)
    }

    subscriptions = Subscriptions.get_active_subscriptions_for_a_type(
        request,
        types.REPLY_TYPE
    )
    for subscription in subscriptions:
        data['subscription'] = subscription.__json__(request)

        # Validate annotation
        if check_conditions(annotation, data):
            try:
                # Render e-mail parts
                tmap = create_template_map(request, annotation, data)
                text = render(TXT_TEMPLATE, tmap, request).strip()
                html = render(HTML_TEMPLATE, tmap, request).strip()
                subject = render(SUBJECT_TEMPLATE, tmap, request).strip()
                recipients = get_recipients(request, data)
                send_email(request, subject, text, html, recipients)
            # ToDo: proper exception handling here
            except TemplateRenderException:
                log.exception('Failed to render subscription'
                              ' template %s', subscription)
            except:
                log.exception('Unknown error when trying to render'
                              ' subscription template %s', subscription)


# Create a reply template for a uri
def create_subscription(request, uri, active):
    session = get_session(request)
    subs = Subscriptions(
        uri=uri,
        type=types.REPLY_TYPE,
        active=active
    )

    session.add(subs)
    session.flush()


@subscriber(NewRegistrationEvent)
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
    res = Subscriptions.get_templates_for_uri_and_type(
        request,
        user_uri,
        types.REPLY_TYPE
    )
    if not len(res):
        create_subscription(event.request, user_uri, True)
        event.user.subscriptions = True


def includeme(config):
    config.scan(__name__)
