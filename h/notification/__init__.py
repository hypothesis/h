# -*- coding: utf-8 -*-
from webob.cookies import SignedSerializer


def includeme(config):
    config.include('.types')
    config.include('.gateway')
    config.include('.models')
    config.include('.notifier')
    config.include('.reply_template')
    config.include('.views')

    # We use the shared session secret, but salt it with the namespace
    # 'h.notification' -- only messages serialized with this salt will
    # authenticate on deserialization.
    secret = config.registry.settings['session.secret']
    serializer = SignedSerializer(secret, 'h.notification')
    config.registry.notification_serializer = serializer
