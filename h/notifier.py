
import traceback
import re

from pyramid_mailer.interfaces import IMailer
from pyramid_mailer.message import Message
from pyramid_mailer.testing import DummyMailer

from pyramid.renderers import render

from pyramid.events import subscriber
from h import events, models
from h.interfaces import IStoreClass

import logging
log = logging.getLogger(__name__)

class AnnotationDummyMailer(DummyMailer):
    def __init__(self):
        super(AnnotationDummyMailer, self).__init__()

class AnnotationNotifier(object):
    def __init__(self, request):
        self.request = request
        self.registry = request.registry
        self.mailer = self.registry.queryUtility(IMailer)
        self.store = self.registry.queryUtility(IStoreClass)(request)

    @property
    def template(self):
        return 'h:templates/emails/reply_notification.pt'

    def send_notification_to_owner(self, annotation, action):
        # Get the e-mail of the owner
        parent = self.store.read(annotation['references'][-1])
        username = re.search("^acct:([^@]+)", parent['user']).group(1)
        userobj = models.User.get_by_username(self.request, username)
        recipients = [userobj.email]
        self._send_annotation(annotation, recipients)

    def _send_annotation(self, annotation, recipients):
        body = render(self.template, {"text": annotation['text']}, self.request)

        message = Message(subject="Re",
                          sender="noreply@hypothes.is",
                          recipients=recipients,
                          body=body)
        self.mailer.send(message)
        log.info('sent: %s' % message.to_message().as_string())


def filter_notifications(annotation, action):
    # For now, we only filter for newly created replies
    if action == 'create' and 'references' in annotation and len(annotation['references']) > 0:
        return True

    return False

@subscriber(events.AnnotationEvent)
def send_notifications(event):
    log.info('send_notifications')
    try:
        action = event.action
        annotation = event.annotation

        if not filter_notifications(annotation, action):
            return

        request = event.request
        notifier = AnnotationNotifier(request)
        notifier.send_notification_to_owner(annotation, action)
    except:
        log.info(traceback.format_exc())
        log.info('Unexpected error occurred in send_notifications(): ' + str(event))


def includeme(config):
    config.scan(__name__)
    mailer = AnnotationDummyMailer()
    config.registry.registerUtility(mailer, IMailer)
