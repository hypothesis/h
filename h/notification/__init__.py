from webob.cookies import SignedSerializer

from ..security import derive_key


def includeme(config):
    config.include(".reply")

    secret = config.registry.settings["secret_key"]
    salt = config.registry.settings["secret_salt"]
    derived = derive_key(secret, salt, b"h.notification")

    config.registry.notification_serializer = SignedSerializer(derived, None)
