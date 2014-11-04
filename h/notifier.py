# -*- coding: utf-8 -*-
import re
import logging
from datetime import datetime

from pyramid_mailer.interfaces import IMailer
from pyramid_mailer.message import Message
from pyramid.renderers import render
from pyramid.events import subscriber

from h import events, interfaces
from h.auth.local import models

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def user_profile_url(request, user):
    username = re.search("^acct:([^@]+)", user).group(1)
    return request.application_url + '/u/' + username


def standalone_url(request, annotation_id):
    return request.application_url + '/a/' + annotation_id


def parent_values(annotation, request):
    if 'references' in annotation:
        registry = request.registry
        store = registry.queryUtility(interfaces.IStoreClass)(request)
        parent = store.read(annotation['references'][-1])
        if 'references' in parent:
            grandparent = store.read(parent['references'][-1])
            parent['quote'] = grandparent['text']

        return parent
    else:
        return {}


class NotificationTemplate(object):
    text_template = None
    html_template = None
    subject = None

    @classmethod
    def render(cls, request, annotation, data):
        tmap = cls._create_template_map(request, annotation, data)
        text = render(cls.text_template, tmap, request)
        html = render(cls.html_template, tmap, request)
        subject = render(cls.subject, tmap, request)
        return subject, text, html

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
            subject, text, html = cls.render(request, annotation, data)
            recipients = cls.get_recipients(request, annotation, data)
        except TemplateRenderException:
            return {'status': False}

        return {
            'status': True,
            'recipients': recipients,
            'text': text,
            'html': html,
            'subject': subject
        }


class TemplateRenderException(Exception):
    pass


class ReplyTemplate(NotificationTemplate):
    text_template = 'h:templates/emails/reply_notification.txt'
    html_template = 'h:templates/emails/reply_notification.html'
    subject = 'h:templates/emails/reply_notification_subject.txt'

    @staticmethod
    def _create_template_map(request, reply, data):
        document_title = ''
        if 'document' in reply:
            document_title = reply['document'].get('title', '')

        parent_user = re.search(
            r'^acct:([^@]+)',
            data['parent']['user']
        ).group(1)

        reply_user = re.search(
            r'^acct:([^@]+)',
            reply['user']
        ).group(1)

        # Currently we cut the UTC format because time.strptime has problems
        # parsing it, and of course it'd only correct the backend's timezone
        # which is not meaningful for international users
        format = '%Y-%m-%dT%H:%M:%S.%f'
        parent_timestamp = datetime.strptime(data['parent']['created'][:-6],
                                             format)
        reply_timestamp = datetime.strptime(reply['created'][:-6], format)

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

    @staticmethod
    def get_recipients(request, annotation, data):
        username = re.search(
            r'^acct:([^@]+)',
            data['parent']['user']
        ).group(1)
        userobj = models.User.get_by_username(request, username)
        if not userobj:
            log.warn("User not found! " + str(username))
            raise TemplateRenderException('User not found')
        return [userobj.email]

    @staticmethod
    def check_conditions(annotation, data):
        # Get the e-mail of the owner
        if 'user' not in data['parent'] or not data['parent']['user']:
            return False
        # Do not notify users about their own replies
        if annotation['user'] == data['parent']['user']:
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
                    notification['subject'],
                    notification['text'],
                    notification['html'],
                    notification['recipients']
                )

    def _send_annotation(self, subject, text, html, recipients):
        body = text.decode('utf8')
        subject = subject.decode('utf8')
        message = Message(subject=subject,
                          recipients=recipients,
                          body=body,
                          html=html)
        self.mailer.send(message)

AnnotationNotifier.register_template(
    'reply_notification',
    ReplyTemplate.generate_notification
)


@subscriber(events.AnnotationEvent)
def send_notifications(event):
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
    # Store the parent values as additional data
    data = {
        'parent': parent_values(annotation, request)
    }

    if 'user' in data['parent'] and 'user' in annotation:
        parent_user = data['parent']['user']
        if len(parent_user) and parent_user != annotation['user']:
            notifier.send_notification_to_owner(
                annotation, data, 'reply_notification')


def includeme(config):
    config.scan(__name__)
