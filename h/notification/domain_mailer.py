# -*- coding: utf-8 -*-
import re
import logging
from urlparse import urlparse

import requests
from bs4 import BeautifulSoup
from pyramid.events import subscriber
from pyramid.renderers import render
from pyramid.security import Everyone, principals_allowed_by_permission

from h import events
from h.notification.gateway import user_profile_url, standalone_url
from h.notification.notifier import send_email, TemplateRenderException
from h.notification.types import ROOT_PATH

log = logging.getLogger(__name__)  # pylint: disable=invalid-name

TXT_TEMPLATE = ROOT_PATH + 'document_owner_notification.txt'
HTML_TEMPLATE = ROOT_PATH + 'document_owner_notification.pt'
SUBJECT_TEMPLATE = ROOT_PATH + 'document_owner_notification_subject.txt'


# ToDo: Turn this feature into uri based.
# Add page uris to the subscriptions table
# And then the domain mailer can be configured to separate web-pages
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
    if event.action != 'create':
        return
    try:
        annotation = event.annotation
        request = event.request

        # Check for authorization. Send notification only for public annotation
        # XXX: This will be changed and fine grained when
        # user groups will be introduced
        allowed = principals_allowed_by_permission(annotation, 'read')
        if Everyone not in allowed:
            return

        uri = annotation['uri']
        # TODO: Fetching the page should be done via a webproxy
        r = requests.get(uri)
        emails = get_document_owners(r.text)

        # Now send the notifications
        url_struct = urlparse(annotation['uri'])
        domain = url_struct.hostname or url_struct.path
        domain = re.sub(r'^www.', '', domain)

        for email in emails:
            # Domain matching
            mail_domain = email.split('@')[-1]
            if mail_domain == domain:
                try:
                    # Render e-mail parts
                    tmap = create_template_map(request, annotation)
                    text = render(TXT_TEMPLATE, tmap, request)
                    html = render(HTML_TEMPLATE, tmap, request)
                    subject = render(SUBJECT_TEMPLATE, tmap, request)
                    send_email(request, subject, text, html, [email])

                # ToDo: proper exception handling here
                except TemplateRenderException:
                    log.exception('Failed to render domain-mailer template')
                except:
                    log.exception(
                        'Unknown error when trying to render'
                        'domain-mailer template')
    except:
        log.exception('Problem with domain notification')


def includeme(config):
    config.scan(__name__)
