# -*- coding: utf-8 -*-
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

backend = default_backend()


def derive_key(key_material, info, algorithm=None, length=None):
    if algorithm is None:
        algorithm = hashes.SHA512()
    if length is None:
        length = algorithm.digest_size
    hkdf = HKDF(algorithm, length, 'h.security', info, backend)
    return hkdf.derive(key_material)
