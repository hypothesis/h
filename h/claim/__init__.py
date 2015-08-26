# -*- coding: utf-8 -*-
from webob.cookies import SignedSerializer

from ..security import derive_key


def includeme(config):
    config.include('.views')
    config.include('.util')
    secret = config.registry.settings['secret_key']
    derived = derive_key(secret, 'h.claim')
    serializer = SignedSerializer(derived, None)
    config.registry.claim_serializer = serializer
