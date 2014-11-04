# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from pyramid.view import view_config
from pyramid_layout.layout import layout_config
from pyramid_mailer.interfaces import IMailer
from pyramid_mailer.testing import DummyMailer
from pyramid.renderers import render

from h.layouts import BaseLayout
from h.notifier import ReplyTemplate

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@view_config(layout='pattern_library',
             renderer='h:templates/pattern_library.html',
             route_name='pattern_library')
def page(context, request):
    return {}


@view_config(renderer='h:templates/email_preview.html',
             route_name='email_preview')
def email_preview(context, request):
    notification_email_data = {
        'document_title': 'A very important article',
        'document_path': 'http://example.com/article?some-long=query',
        'parent_text': 'This is the parent comment',
        'parent_user': 'toby',
        'parent_tags': 'comment, important, news',
        'parent_timestamp': datetime.now() - timedelta(hours=1),
        'parent_user_profile': 'https://hypothes.is/u/toby',
        'parent_path': 'https://hypothes.is/a/123456789',
        'reply_text': 'This is a reply to the parent comment',
        'reply_user': 'anna',
        'reply_timestamp': datetime.now(),
        'reply_user_profile': 'https://hypothes.is/u/anna',
        'reply_path': 'http://hypothes.is/a/abcdefghijk',
    }

    return {
        'emails': (
            {
                'title': 'Notification Email',
                'subject': render(ReplyTemplate.subject,
                                  notification_email_data, request),
                'text': render(ReplyTemplate.text_template,
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
    class Destination(list):
        def __init__(self, prefix):
            self.prefix = prefix

        def append(self, message):
            message.sender = message.sender or 'Default Sender'
            log.info('%s:\n%s', self.prefix, message.to_message().as_string())
            list.append(self, message)

    def __init__(self):
        self.outbox = self.Destination('Sending email')
        self.queue = self.Destination('Queuing email')


def includeme(config):
    config.include('pyramid_layout')

    config.add_route('pattern_library', '/dev/pattern-library')
    config.add_route('email_preview', '/dev/emails')

    mailer = LoggingMailer()
    config.registry.registerUtility(mailer, IMailer)

    config.scan(__name__)
