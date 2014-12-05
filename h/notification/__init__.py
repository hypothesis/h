# -*- coding: utf-8 -*-
from webob.cookies import SignedSerializer


def includeme(config):
    config.include('.types')
    config.include('.gateway')
    config.include('.models')
    config.include('.notifier')
    config.include('.reply_template')
    config.include('.views')

    secret = config.registry.settings['h.notification.secret']
    serializer = SignedSerializer(secret, 'h.notification.secret')
    config.registry.notification_serializer = serializer
