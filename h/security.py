# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import base64
import hashlib
import os

from hkdf import hkdf_expand, hkdf_extract
from passlib.context import CryptContext

DEFAULT_ENTROPY = 32

# We use a passlib CryptContext to define acceptable hashing algorithms for
# passwords. This allows us to easily
#
# - migrate to new hashing algorithms
# - update the number of rounds used when hashing passwords
#
# simply by using the verify_and_update method of the CryptContext object. See
# the passlib documentation on hash migration for more details:
#
#   https://pythonhosted.org/passlib/lib/passlib.context-tutorial.html#context-migration-example
#
password_context = CryptContext(
    schemes=["bcrypt"], bcrypt__ident="2b", bcrypt__min_rounds=12
)


def derive_key(key_material, salt, info):
    """
    Derive a fixed-size (64-byte) key for use in cryptographic operations.

    The key is derived using HKDF with the SHA-512 hash function. See
    https://tools.ietf.org/html/rfc5869.

    :type key_material: str or bytes
    :type salt: bytes
    :type info: bytes
    """
    if not isinstance(key_material, bytes):
        key_material = key_material.encode()

    pseudorandom_key = hkdf_extract(salt, key_material, hash=hashlib.sha512)
    return hkdf_expand(pseudorandom_key, info, length=64, hash=hashlib.sha512)


# Implementation modeled on `secrets.token_urlsafe`, new in Python 3.6.
def token_urlsafe(nbytes=None):
    """Return a random URL-safe string composed of *nbytes* random bytes."""
    if nbytes is None:
        nbytes = DEFAULT_ENTROPY
    tok = os.urandom(nbytes)
    return base64.urlsafe_b64encode(tok).rstrip(b"=").decode("ascii")
