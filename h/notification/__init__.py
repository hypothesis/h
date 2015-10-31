# -*- coding: utf-8 -*-
from webob.cookies import SignedSerializer

from ..security import derive_key


class FallbackSerializer(object):
    """
    A message serializer/deserializer which can try a number of serializers in
    turn. For backwards compatibility only.
    """

    def __init__(self, serializers):
        if not len(serializers) > 0:
            raise ValueError('you must provide at least one serializer')
        self.serializers = serializers

    def dumps(self, appstruct):
        return self.serializers[0].dumps(appstruct)

    def loads(self, bstruct):
        for s in self.serializers[:-1]:
            try:
                return s.loads(bstruct)
            except ValueError:
                continue
        return self.serializers[-1].loads(bstruct)


def includeme(config):
    config.include('.types')
    config.include('.gateway')
    config.include('.notifier')
    config.include('.reply_template')
    config.include('.views')

    secret = config.registry.settings['secret_key']
    derived = derive_key(secret, b'h.notification')

    old_serializer = SignedSerializer(secret, 'h.notification')
    new_serializer = SignedSerializer(derived, None)

    # Create all new notification tokens with the new serializer, but, for now,
    # allow ones created with the old serializer to deserialize correctly.
    #
    # bw compat -- remove after an acceptable changeover period.
    serializer = FallbackSerializer([new_serializer, old_serializer])
    config.registry.notification_serializer = serializer
