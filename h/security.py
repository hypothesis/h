import hashlib
import hmac


def derive_key(secret, salt):
    if secret is None:
        raise ValueError('secret must be supplied')
    if salt is None:
        raise ValueError('salt must be supplied')
    mac = hmac.new(secret, msg=salt, digestmod=hashlib.sha512)
    return mac.digest()
