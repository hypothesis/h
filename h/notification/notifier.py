# -*- coding: utf-8 -*-
import logging

from pyramid_mailer.interfaces import IMailer
from pyramid_mailer.message import Message
from pyramid.renderers import render
from pyramid.events import subscriber

from h import events, interfaces
from h.notification.models import Subscriptions

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


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

    subscriptions = Subscriptions.get_active_subscriptions(request)
    for subscription in subscriptions:
        data['subscription'] = {
            'uri': subscription.uri,
            'parameters': subscription.parameters,
            'query': subscription.query
        }

        notifier.send_notification_to_owner(
            annotation, data, subscription.template)


def includeme(config):
    config.scan(__name__)
