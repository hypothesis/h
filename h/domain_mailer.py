import re
from urlparse import urlparse

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


@subscriber(events.AnnotationEvent)
def domain_notification(event):
    if event.action == 'create':
        annotation = event.annotation
        if 'document' in annotation and 'reply_to' in annotation['document']:
            url_struct = urlparse(annotation['uri'])
            domain = url_struct.hostname if len(url_struct.hostname) > 0 else url_struct.path
            if domain[0:4] == 'www.': domain = domain[4:]
            notifier = AnnotationNotifier(event.request)
            for email in annotation['document']['reply_to']:
                # Domain matching
                mail_domain = email.split('@')[-1]
                if mail_domain == domain:
                    # Send notification to owners
                    notifier.send_notification_to_owner(annotation, {'email': email}, 'document_owner')


def includeme(config):
    config.scan(__name__)