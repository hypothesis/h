from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand
from cryptography.hazmat.backends import default_backend

backend = default_backend()


def derive_key(key_material, info, algorithm=None, length=32):
    if algorithm is None:
        algorithm = hashes.SHA256()
    return HKDFExpand(algorithm, length, info, backend).derive(key_material)
