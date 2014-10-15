# -*- coding: utf-8 -*-
import re
import logging
from urlparse import urlparse

import requests
from bs4 import BeautifulSoup
from pyramid.events import subscriber

from h import events
from h.notification.gateway import user_profile_url, standalone_url
from h.notification.types import DOCUMENT_OWNER
import h.notification.notifier as notifier

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def create_template_map(request, annotation):
    if 'tags' in annotation:
        tags = '\ntags: ' + ', '.join(annotation['tags'])
    else:
        tags = ''
    user = re.search("^acct:([^@]+)", annotation['user']).group(1)
    return {
        'document_title': annotation['title'],
        'document_path': annotation['uri'],
        'text': annotation['text'],
        'tags': tags,
        'user_profile': user_profile_url(request, annotation['user']),
        'user': user,
        'path': standalone_url(request, annotation['id']),
        'timestamp': annotation['created'],
        'selection': annotation['quote']
    }


def get_recipients(request, annotation, data):
    return [data['email']]


def check_conditions(annotation, data):
    return True

# Register the template
notifier.AnnotationNotifier.register_template(
    DOCUMENT_OWNER, {
        'template': 'h:notification/templates/emails/document_owner_notification.txt',
        'html_template': 'h:notification/templates/emails/document_owner_notification.pt',
        'subject': 'h:notification/templates/emails/document_owner_notification_subject.txt',
        'template_map': create_template_map,
        'recipients': get_recipients,
        'conditions': check_conditions
    }
)


# TODO: Introduce proper cache for content parsing
def get_document_owners(content):
    parsed_data = BeautifulSoup(content)
    documents = parsed_data.select('a[rel="reply-to"]')
    hrefs = []
    for d in documents:
        if re.match(r'^mailto:', d['href'], re.IGNORECASE):
            hrefs.append(d['href'][7:])

    return hrefs


# XXX: All below can be removed in the future after
# we can create a custom subscription for page uri
@subscriber(events.AnnotationEvent)
def domain_notification(event):
    if event.action == 'create':
        try:
            annotation = event.annotation

            # Check for authorization. Send notification only for public
            # annotation
            # XXX: This can be changed and fine grained when user
            # groups will be introduced
            read = annotation['permissions']['read']
            if "group:__world__" not in read:
                return

            uri = annotation['uri']
            # TODO: Fetching the page should be done via a webproxy
            r = requests.get(uri)
            emails = get_document_owners(r.text)

            # Now send the notifications
            url_struct = urlparse(annotation['uri'])
            domain = url_struct.hostname or url_struct.path
            domain = re.sub(r'^www.', '', domain)
            notif = notifier.AnnotationNotifier(event.request)
            for email in emails:
                # Domain matching
                mail_domain = email.split('@')[-1]
                if mail_domain == domain:
                    try:
                        # Send notification to owners
                        notif.send_notification_to_owner(
                            annotation,
                            {'email': email},
                            DOCUMENT_OWNER
                        )
                    except:
                        log.exception('Problem sending email')
        except:
            log.exception('Problem with domain notification')


def includeme(config):
    config.scan(__name__)
