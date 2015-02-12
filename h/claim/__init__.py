from webob.cookies import SignedSerializer


def includeme(config):
    config.include('.views')
    config.include('.util')

    # We use the shared session secret, but salt it with the namespace
    # 'h.claim' -- only messages serialized with this salt will
    # authenticate on deserialization.
    secret = config.registry.settings['session.secret']
    serializer = SignedSerializer(secret, 'h.claim')
    config.registry.claim_serializer = serializer
