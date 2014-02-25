import re
from urlparse import urlparse
import requests
import requests_cache
#import Queue
from gevent.queue import Queue
from BeautifulSoup import BeautifulSoup
import threading
import time

from pyramid.events import subscriber
from pyramid.renderers import render
from h import events
from h.notifier import user_profile_url, standalone_url, AnnotationNotifier

import logging
log = logging.getLogger(__name__)


class DocumentOwnerNotificationTemplate(object):
    template = 'h:templates/emails/document_owner_notification.pt'

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
        }

    @staticmethod
    def render(request, annotation):
        return render(DocumentOwnerNotificationTemplate.template,
                      DocumentOwnerNotificationTemplate._create_template_map(request, annotation),
                      request)

    @staticmethod
    def generate_notification(request, annotation, data):
        recipients = [data['email']]
        rendered = DocumentOwnerNotificationTemplate.render(request, annotation)
        subject = "New annotation in your page: " + annotation['title'] + \
                  "(" + annotation['uri'] + ")"
        return {
            'status': True,
            'recipients': recipients,
            'rendered': rendered,
            'subject': subject
        }

AnnotationNotifier.register_template('document_owner', DocumentOwnerNotificationTemplate.generate_notification)

requests_cache.install_cache('document_cache')
document_cache = {}
notifications = Queue()


def notification_worker():
    log.info('---- Init worker ----')
    while True:
        if not notifications.empty():
            log.info('--------- Trying to get --------------')
            annotation, request = notifications.get()
            uri = annotation['uri']
            log.info('---- Got new URI ----')
            log.info(uri)
            r = requests.get(uri)
            log.info('---- Got answer ----')
            log.info(r.headers)
            page_date = r.headers.last_modified

            # Check if the page is not cached or the cache is old
            if uri not in document_cache or document_cache[uri]['date'] != page_date:
                log.info('---- Begin parsing ----')
                parsed_data = BeautifulSoup(r.data)
                documents = parsed_data.select('a[rel="reply-to"]')
                hrefs = [d['href'] for d in documents]
                log.info(hrefs)
                document_cache[uri] = {
                    'date': page_date,
                    'hrefs': hrefs
                }

            # Now send the notifications
            emails = document_cache[uri]
            url_struct = urlparse(annotation['uri'])
            domain = url_struct.hostname if len(url_struct.hostname) > 0 else url_struct.path
            if domain[0:4] == 'www.': domain = domain[4:]
            notifier = AnnotationNotifier(request)
            for email in emails:
                # Domain matching
                mail_domain = email.split('@')[-1]
                if mail_domain == domain:
                    # Send notification to owners
                    notifier.send_notification_to_owner(annotation, {'email': email}, 'document_owner')
            notifications.task_done()
        else:
            time.sleep(1)
            log.info(notifications.qsize())


@subscriber(events.AnnotationEvent)
def domain_notification(event):
    log.info('event!!!!')
    if event.action == 'create':
        log.info('put')
        notifications.put(event)
        log.info(notifications.qsize())
        log.info('after put')

worker = threading.Thread(target=notification_worker)
worker.daemon = True
worker.start()


def includeme(config):
    config.scan(__name__)