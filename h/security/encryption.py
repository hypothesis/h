import base64
import os
from typing import cast

from Cryptodome.Hash import SHA512
from Cryptodome.Protocol.KDF import HKDF
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


def derive_key(key_material: str | bytes, salt: bytes, info: bytes) -> bytes:
    """
    Derive a fixed-size (64-byte) key for use in cryptographic operations.

    The key is derived using HKDF with the SHA-512 hash function. See
    https://tools.ietf.org/html/rfc5869.

    :arg key_material: High-entropy secret used to derive key
    :arg salt: Non-secret value used to strengthen generation. Ideally as long
         as the hash digest (64 bytes)
    :arg info: Identifier describing what the key is for
    """
    if not isinstance(key_material, bytes):
        key_material = key_material.encode()

    return cast(
        bytes,
        HKDF(
            master=key_material,
            key_len=64,
            salt=salt,
            hashmod=SHA512,
            num_keys=1,
            context=info,
        ),
    )


# If we have problems with PyCryptodome, an alternative implementation using
# cryptography would be:

# from cryptography.hazmat.primitives.kdf.hkdf import HKDF as HKDF2  # noqa: ERA001
# from cryptography.hazmat.primitives import hashes  # noqa: ERA001
#
# def derive_key(key_material, salt, info):
#     if not isinstance(key_material, bytes):
#         key_material = key_material.encode()  # noqa: ERA001
#
#     return HKDF2(
#         algorithm=hashes.SHA512(), length=64, salt=salt, info=info
#     ).derive(key_material)


# Implementation modeled on `secrets.token_urlsafe`, new in Python 3.6.
def token_urlsafe(nbytes=None) -> str:
    """Return a random URL-safe string composed of *nbytes* random bytes."""
    if nbytes is None:
        nbytes = DEFAULT_ENTROPY
    tok = os.urandom(nbytes)
    return base64.urlsafe_b64encode(tok).rstrip(b"=").decode("ascii")
