# -*- coding: utf-8 -*-
from pyramid_mailer.interfaces import IMailer
from pyramid_mailer.message import Message


class TemplateRenderException(Exception):
    pass


def send_email(request, subject, text, html, recipients):
    body = text.decode('utf8')
    mailer = request.registry.queryUtility(IMailer)
    subject = subject.decode('utf8')
    message = Message(subject=subject,
                      recipients=recipients,
                      body=body,
                      html=html)
    mailer.send(message)


def includeme(config):
    config.scan(__name__)
