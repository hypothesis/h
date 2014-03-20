import re
import logging
from urlparse import urlparse
import traceback

import requests
from bs4 import BeautifulSoup

from pyramid.events import subscriber

from h import events
from h.notifier import user_profile_url, standalone_url, AnnotationNotifier, NotificationTemplate

log = logging.getLogger(__name__)


class DocumentOwnerTemplate(NotificationTemplate):
    template = 'h:templates/emails/document_owner_notification.txt'
    subject = 'h:templates/emails/document_owner_notification_subject.txt'

    @staticmethod
    def _create_template_map(request, annotation):
        tags = '\ntags: ' + ', '.join(annotation['tags']) if 'tags' in annotation else ''
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

    @staticmethod
    def get_recipients(request, annotation, data):
        return [data['email']]


AnnotationNotifier.register_template('document_owner', DocumentOwnerTemplate.generate_notification)


# TODO: Introduce proper cache for content parsing
def get_document_owners(content):
    parsed_data = BeautifulSoup(content)
    documents = parsed_data.select('a[rel="reply-to"]')
    hrefs = []
    for d in documents:
        if d['href'].lower()[0:7] == 'mailto:': hrefs.append(d['href'][7:])

    return hrefs


@subscriber(events.AnnotationEvent)
def domain_notification(event):
    if event.action == 'create':
        try:
            annotation = event.annotation
            uri = annotation['uri']
            # TODO: Fetching the page should be done via a webproxy
            r = requests.get(uri)
            emails = get_document_owners(r.text)

            # Now send the notifications
            url_struct = urlparse(annotation['uri'])
            domain = url_struct.hostname if len(url_struct.hostname) > 0 else url_struct.path
            if domain[0:4] == 'www.': domain = domain[4:]
            notifier = AnnotationNotifier(event.request)
            for email in emails:
                # Domain matching
                mail_domain = email.split('@')[-1]
                if mail_domain == domain:
                    try:
                        # Send notification to owners
                        notifier.send_notification_to_owner(annotation, {'email': email}, 'document_owner')
                    except:
                        log.exception(traceback.format_exc())
                        log.exception('Failed to send email!')
        except:
            log.exception(traceback.format_exc())
            log.exception('Notification_worker error!')


def includeme(config):
    config.scan(__name__)