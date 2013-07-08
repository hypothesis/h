import logging

from pyramid_mailer.interfaces import IMailer
from pyramid_mailer.testing import DummyMailer

log = logging.getLogger(__name__)


class LoggingMailer(DummyMailer):
    def __init__(self):
        super(LoggingMailer, self).__init__()

    def send(self, message):
        if not message.sender: message.sender = 'fake@localhost'
        super(LoggingMailer, self).send(message)
        log.info('sent: %s' % message.to_message().as_string())

    def send_immediately(self, message, fail_silently=False):
        if not message.sender: message.sender = 'fake@localhost'
        super(LoggingMailer, self).send_immediately(message, fail_silently)
        log.info('sent immediately: %s' % message.to_message().as_string())

    def send_to_queue(self, message):
        if not message.sender: message.sender = 'fake@localhost'
        super(LoggingMailer, self).send_to_queue(message)
        log.info('queued: %s' % message.to_message().as_string())


def includeme(config):
    mailer = LoggingMailer()
    config.registry.registerUtility(mailer, IMailer)
