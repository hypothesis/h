# -*- coding: utf-8 -*-
from webob.cookies import SignedSerializer

from ..security import derive_key


def includeme(config):
    config.include('.types')
    config.include('.gateway')
    config.include('.notifier')
    config.include('.reply_template')
    config.include('.views')

    secret = config.registry.settings['secret_key']
    derived = derive_key(secret, b'h.notification')

    config.registry.notification_serializer = SignedSerializer(derived, None)
