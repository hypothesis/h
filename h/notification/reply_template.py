# -*- coding: utf-8 -*-
import logging
import transaction
from datetime import datetime

from pyramid.events import subscriber
from hem.db import get_session
from horus.events import NewRegistrationEvent


import h.notification.notifier as notifier
from h.notification.types import REPLY_TEMPLATE
from h.notification.models import Subscriptions
from h.notification.gateway import user_name, user_profile_url, standalone_url, get_user_by_name

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def create_template_map(request, reply, data):
    document_title = ''
    if 'document' in reply:
        document_title = reply['document'].get('title', '')

    parent_user = user_name(data['parent']['user'])
    reply_user = user_name(reply['user'])

    # Currently we cut the UTC format because time.strptime has problems
    # parsing it, and of course it'd only correct the backend's timezone
    # which is not meaningful for international users
    date_format = '%Y-%m-%dT%H:%M:%S.%f'
    parent_timestamp = datetime.strptime(data['parent']['created'][:-6], date_format)
    reply_timestamp = datetime.strptime(reply['created'][:-6], date_format)

    return {
        'document_title': document_title,
        'document_path': data['parent']['uri'],
        'parent_text': data['parent']['text'],
        'parent_user': parent_user,
        'parent_timestamp': parent_timestamp,
        'parent_user_profile': user_profile_url(
            request, data['parent']['user']),
        'parent_path': standalone_url(request, data['parent']['id']),
        'reply_text': reply['text'],
        'reply_user': reply_user,
        'reply_timestamp': reply_timestamp,
        'reply_user_profile': user_profile_url(request, reply['user']),
        'reply_path': standalone_url(request, reply['id'])
    }


def get_recipients(request, annotation, data):
    username = user_name(data['parent']['user'])
    user_obj = get_user_by_name(request, username)
    if not user_obj:
        log.warn("User not found! " + str(username))
        raise notifier.TemplateRenderException('User not found')
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

# Register the template
notifier.AnnotationNotifier.register_template(
    REPLY_TEMPLATE, {
        'text_template': 'h:notification/templates/reply_notification.txt',
        'html_template': 'h:notification/templates/reply_notification.pt',
        'subject': 'h:notification/templates/reply_notification_subject.txt',
        'template_map': create_template_map,
        'recipients': get_recipients,
        'conditions': check_conditions
    }
)


# Create a reply template for a uri
def create_subscription(request, uri, active):
    session = get_session(request)
    subs = Subscriptions(
        uri=uri,
        template=REPLY_TEMPLATE,
        description='Generated reply notification template',
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


def includeme(config):
    config.scan(__name__)
