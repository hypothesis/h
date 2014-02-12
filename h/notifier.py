import traceback
import re

from pyramid_mailer.interfaces import IMailer
from pyramid_mailer.message import Message
from pyramid_mailer.testing import DummyMailer

from pyramid.renderers import render

from pyramid.events import subscriber
from h import events, models
from h.interfaces import IStoreClass
from h.streamer import FilterHandler

import logging
log = logging.getLogger(__name__)


def user_profile_url(request, user):
    username = re.search("^acct:([^@]+)", user).group(1)
    return request.application_url + '/u/' + username


def standalone_url(request, id):
    return request.application_url + '/a/' + id


class ReplyTemplate(object):
    template = 'h:templates/emails/reply_notification.pt'

    @staticmethod
    def _create_template_map(request, reply, parent):
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
            'parent_user_profile': user_profile_url(request, parent['user']),
            'parent_path': standalone_url(request, parent['id']),
            'reply_quote': reply['quote'],
            'reply_text': reply['text'],
            'reply_user': reply_user,
            'reply_tags': reply_tags,
            'reply_timestamp': reply['created'],
            'reply_user_profile': user_profile_url(request, reply['user']),
            'reply_path': standalone_url(request, reply['id'])
        }

    @staticmethod
    def render(request, reply, parent):
        return render(ReplyTemplate.template, ReplyTemplate._create_template_map(request, reply, parent), request)


class CustomSearchTemplate(object):
    template = 'h:templates/emails/custom_search.pt'

    @staticmethod
    def _create_template_map(request, annotation):
        tags = ', '.join(annotation['tags']) if 'tags' in annotation else '(none)'
        return {
            'document_title': annotation['title'],
            'document_path': annotation['uri'],
            'text': annotation['text'],
            'tags': tags,
            'user_profile': user_profile_url(request, annotation['user']),
            'path': standalone_url(request, annotation['id'])
        }

    @staticmethod
    def render(request, annotation):
        return render(CustomSearchTemplate.template,
                      CustomSearchTemplate._create_template_map(request, annotation),
                      request)


class AnnotationDummyMailer(DummyMailer):
    def __init__(self):
        super(AnnotationDummyMailer, self).__init__()


class AnnotationNotifier(object):
    def __init__(self, request):
        self.request = request
        self.registry = request.registry
        self.mailer = self.registry.queryUtility(IMailer)
        self.store = self.registry.queryUtility(IStoreClass)(request)


    def send_notification_to_owner(self, annotation, template):
        if template == 'reply_notification':
            # Get the e-mail of the owner
            parent = self.store.read(annotation['references'][-1])

            if not ('quote' in parent):
                grandparent = self.store.read(parent['references'][-1])
                parent['quote'] = grandparent['text']
            # Do not notify me about my own message
            if not parent['user']: return
            if annotation['user'] == parent['user']: return

            username = re.search("^acct:([^@]+)", parent['user']).group(1)
            userobj = models.User.get_by_username(self.request, username)
            if not userobj:
                log.warn("Warning! User not found! " + str(username))
                return
            recipients = [userobj.email]
            rendered = ReplyTemplate.render(self.request, annotation, parent)
            subject = "Reply for your annotation [" + parent['id'] + ']'
            self._send_annotation(rendered, subject, recipients)
        elif template == 'custom_search':
            username = re.search("^acct:([^@]+)", annotation['user']).group(1)
            userobj = models.User.get_by_username(self.request, username)
            if not userobj:
                log.warn("Warning! User not found! " + str(username))
                return
            recipients = [userobj.email]
            rendered = ReplyTemplate.render(self.request, annotation)
            subject = "New annotation for your query [" + annotation['id'] + "]"
            self._send_annotation(rendered, subject, recipients)

    def _send_annotation(self, body, subject, recipients):
        message = Message(subject=subject,
                          sender="noreply@hypothes.is",
                          recipients=recipients,
                          body=body)
        self.mailer.send(message)
        log.info('sent: %s' % message.to_message().as_string())


@subscriber(events.AnnotationEvent)
def send_notifications(event):
    log.info('send_notifications')
    try:
        action = event.action
        annotation = event.annotation
        request = event.request
        notifier = AnnotationNotifier(request)

        queries = models.UserQueries.get_all(request).all()
        for query in queries:
            if FilterHandler(query.query).match(annotation, action):
                # Send it to the template renderer, using the stored template type
                notifier.send_notification_to_owner(annotation, query.template)
    except:
        log.info(traceback.format_exc())
        log.info('Unexpected error occurred in send_notifications(): ' + str(event))


def includeme(config):
    config.scan(__name__)

    #mailer = AnnotationDummyMailer()
    #config.registry.registerUtility(mailer, IMailer)
