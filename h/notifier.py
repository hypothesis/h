
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

        if not ('quote' in parent):
            grandparent = self.store.read(parent['references'][-1])
            parent['quote'] = grandparent['text']
        # Do not notify me about my own message
        if annotation['user'] == parent['user']: return

        username = re.search("^acct:([^@]+)", parent['user']).group(1)
        userobj = models.User.get_by_username(self.request, username)
        if not userobj:
            log.warn("Warning! User not found! " + str(username))
            session = models.get_session(self.request)
            users = session.query(models.User).all()
            log.info('------------------------------------')
            log.info(users)
            log.info('------------------------------------')
            return
        recipients = [userobj.email]
        template_map = self._create_template_map(annotation, parent)
        self._send_annotation(template_map, parent['id'], recipients)

    def _create_template_map(self, reply, parent):
        parent_user = re.search("^acct:([^@]+)", parent['user']).group(1)
        reply_user = re.search("^acct:([^@]+)", reply['user']).group(1)
        parent_tags = ', '.join(parent['tags']) if 'tags' in parent else '(none)'
        reply_tags = ', '.join(reply['tags']) if 'tags' in reply else '(none)'

        return {
            'document_title': reply['title'],
            'document_path': parent['uri'],
            'parent_quote': parent['quote'],
            'parent_text': parent['text'],
            'parent_user': parent_user,
            'parent_tags': parent_tags,
            'parent_timestamp': parent['created'],
            'parent_user_profile': self.request.application_url + '/u/' + parent_user,
            'parent_path': self.request.application_url + '/a/' + parent['id'],
            'reply_quote': reply['quote'],
            'reply_text': reply['text'],
            'reply_user': reply_user,
            'reply_tags': reply_tags,
            'reply_timestamp': reply['created'],
            'reply_user_profile': self.request.application_url + '/u/' + reply_user,
            'reply_path': self.request.application_url + '/a/' + reply['id']
        }

    def _send_annotation(self, template_map, id, recipients):
        body = render(self.template, template_map, id, self.request)

        message = Message(subject="Reply for your annotation [" + id + ']',
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

    #mailer = AnnotationDummyMailer()
    #config.registry.registerUtility(mailer, IMailer)
