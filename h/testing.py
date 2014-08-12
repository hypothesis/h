# -*- coding: utf-8 -*-
import logging

from datetime import datetime, timedelta
from h.notifier import ReplyTemplate
from pyramid.view import view_config
from pyramid_layout.layout import layout_config
from pyramid_mailer.interfaces import IMailer
from pyramid_mailer.testing import DummyMailer
from pyramid.renderers import render

from h.layouts import BaseLayout

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@view_config(layout='pattern_library',
             renderer='h:templates/pattern_library.pt',
             route_name='pattern_library')
def page(context, request):
    return {}

@view_config(renderer='h:templates/email_preview.pt',
             route_name='email_preview')
def page(context, request):
    notification_email_data = {
        'document_title': 'A very important article',
        'document_path': 'http://example.com/article?some-long=query',
        'parent_quote': 'This is a selected piece of text',
        'parent_text': 'This is the parent comment',
        'parent_user': 'toby',
        'parent_tags': 'comment, important, news',
        'parent_timestamp': datetime.now() - timedelta(hours=1),
        'parent_user_profile': 'https://hypothes.is/user:toby',
        'parent_path': 'https://hypothes.is/a/123456789',
        'reply_quote': '',
        'reply_text': 'This is a reply to the parent comment',
        'reply_user': 'anna',
        'reply_tags': 'reply, important, critisism',
        'reply_timestamp': datetime.now(),
        'reply_user_profile': 'https://hypothes.is/user:anna',
        'reply_path': 'http://hypothes.is/a/abcdefghijk',
    }

    return {
        'emails': (
            {
                'title': 'Notification Email',
                'subject': render(ReplyTemplate.subject,
                           notification_email_data, request),
                'text': render(ReplyTemplate.template,
                            notification_email_data, request),
                'html': render(ReplyTemplate.html_template,
                            notification_email_data, request),
            },
        )
    }


@layout_config(name='pattern_library', template='h:templates/base.pt')
class PatternLibraryLayout(BaseLayout):
    requirements = (
        ('app', None),
        ('inject_css', None),
    )


class LoggingMailer(DummyMailer):
    def __init__(self):
        super(LoggingMailer, self).__init__()

    def send(self, message):
        if not message.sender:
            message.sender = 'fake@localhost'
        super(LoggingMailer, self).send(message)
        log.info('sent: %s', message.to_message().as_string())

    def send_immediately(self, message, fail_silently=False):
        if not message.sender:
            message.sender = 'fake@localhost'
        super(LoggingMailer, self).send_immediately(message, fail_silently)
        log.info('sent immediately: %s', message.to_message().as_string())

    def send_to_queue(self, message):
        if not message.sender:
            message.sender = 'fake@localhost'
        super(LoggingMailer, self).send_to_queue(message)
        log.info('queued: %s', message.to_message().as_string())


def includeme(config):
    config.include('pyramid_layout')

    config.add_route('pattern_library', '/dev/pattern-library')
    config.add_route('email_preview', '/dev/emails')

    mailer = LoggingMailer()
    config.registry.registerUtility(mailer, IMailer)

    config.scan(__name__)
