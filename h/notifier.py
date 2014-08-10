# -*- coding: utf-8 -*-
import re
import logging

from pyramid_mailer.interfaces import IMailer
from pyramid_mailer.message import Message
from pyramid.renderers import render
from pyramid.events import subscriber

from h import events
from h.auth.local import models
from h.streamer import parent_values

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def user_profile_url(request, user):
    username = re.search("^acct:([^@]+)", user).group(1)
    return request.application_url + '/u/' + username


def standalone_url(request, annotation_id):
    return request.application_url + '/a/' + annotation_id


class NotificationTemplate(object):
    template = None
    subject = None

    @classmethod
    def render(cls, request, annotation):
        tmap = cls._create_template_map(request, annotation)
        template = render(cls.template, tmap, request)
        subject = render(cls.subject, tmap, request)
        return template, subject

    @staticmethod
    def _create_template_map(request, annotation):
        raise NotImplementedError()

    # Override this for checking
    @staticmethod
    def check_conditions(annotation, data):
        return True

    @staticmethod
    def get_recipients(request, annotation, data):
        raise NotImplementedError()

    @classmethod
    def generate_notification(cls, request, annotation, data):
        checks = cls.check_conditions(annotation, data)
        if not checks:
            return {'status': False}
        try:
            rendered, subject = cls.render(request, annotation)
            recipients = cls.get_recipients(request, annotation, data)
        except:
            log.exception('Generating notification')
            return {'status': False}
        return {
            'status': True,
            'recipients': recipients,
            'rendered': rendered,
            'subject': subject
        }


class ReplyTemplate(NotificationTemplate):
    template = 'h:templates/emails/reply_notification.txt'
    subject = 'h:templates/emails/reply_notification_subject.txt'

    @staticmethod
    def _create_template_map(request, reply):
        parent_tags = ''
        reply_tags = ''
        reply_quote = reply.get('quote', '')

        if 'tags' in reply['parent']:
            parent_tags = '\ntags: ' + ', '.join(reply['parent']['tags'])
        if 'tags' in reply:
            reply_tags = '\ntags: ' + ', '.join(reply['tags'])

        parent_user = re.search(
            r'^acct:([^@]+)',
            reply['parent']['user']
        ).group(1)

        reply_user = re.search(
            r'^acct:([^@]+)',
            reply['user']
        ).group(1)

        return {
            'document_title': reply['title'],
            'document_path': reply['parent']['uri'],
            'parent_quote': reply['parent']['quote'],
            'parent_text': reply['parent']['text'],
            'parent_user': parent_user,
            'parent_tags': parent_tags,
            'parent_timestamp': reply['parent']['created'],
            'parent_user_profile': user_profile_url(request,
                                                    reply['parent']['user']),
            'parent_path': standalone_url(request, reply['parent']['id']),
            'reply_quote': reply_quote,
            'reply_text': reply['text'],
            'reply_user': reply_user,
            'reply_tags': reply_tags,
            'reply_timestamp': reply['created'],
            'reply_user_profile': user_profile_url(request, reply['user']),
            'reply_path': standalone_url(request, reply['id'])
        }

    @staticmethod
    def get_recipients(request, annotation, data):
        username = re.search(
            r'^acct:([^@]+)',
            annotation['parent']['user']
        ).group(1)
        userobj = models.User.get_by_username(request, username)
        if not userobj:
            log.warn("User not found! " + str(username))
            raise Exception('User not found')
        return [userobj.email]

    @staticmethod
    def check_conditions(annotation, data):
        # Get the e-mail of the owner
        if 'user' not in annotation['parent'] or not annotation['parent']['user']:
            return False
        # Do not notify users about their own replies
        if annotation['user'] == annotation['parent']['user']:
            return False
        # Else okay
        return True


class AnnotationNotifier(object):
    registered_templates = {}

    def __init__(self, request):
        self.request = request
        self.registry = request.registry
        self.mailer = self.registry.queryUtility(IMailer)

    @classmethod
    def register_template(cls, template, function):
        cls.registered_templates[template] = function

    def send_notification_to_owner(self, annotation, data, template):
        if template in self.registered_templates:
            generator = self.registered_templates[template]
            notification = generator(self.request, annotation, data)
            if notification['status']:
                self._send_annotation(
                    notification['rendered'],
                    notification['subject'],
                    notification['recipients']
                )

    def _send_annotation(self, body, subject, recipients):
        body = body.decode('utf8')
        subject = subject.decode('utf8')
        message = Message(subject=subject,
                          recipients=recipients,
                          body=body)
        self.mailer.send(message)

AnnotationNotifier.register_template(
    'reply_notification',
    ReplyTemplate.generate_notification
)


@subscriber(events.AnnotationEvent)
def send_notifications(event):
    try:
        action = event.action
        request = event.request
        annotation = event.annotation

        # Now process only the reply-notifications
        # And for them we need only the creation action
        if action != 'create':
            return

        # Check for authorization. Send notification only for public annotation
        # XXX: This will be changed and fine grained when
        # user groups will be introduced
        read = annotation['permissions']['read']
        if "group:__world__" not in read:
            return

        notifier = AnnotationNotifier(request)
        annotation['parent'] = parent_values(annotation, request)
        if 'user' in annotation['parent'] and 'user' in annotation:
            parentuser = annotation['parent']['user']
            if len(parentuser) and parentuser != annotation['user']:
                notifier.send_notification_to_owner(
                    annotation, {}, 'reply_notification')
    except:
        log.exception('Emailing event: %s', event)

def includeme(config):
    config.scan(__name__)
