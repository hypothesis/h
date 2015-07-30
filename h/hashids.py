from __future__ import absolute_import

import hashids


def _get_hashids(request, context):
    salt = request.registry.settings["h.hashids.salt"] + context
    return hashids.Hashids(salt=salt, min_length=6)


def encode(request, context, number):
    """Return a hashid of the given number."""
    return _get_hashids(request, context).encode(number)


def decode(request, context, hashid):
    """Decode the given hashid and return the original number."""
    return _get_hashids(request, context).decode(str(hashid))[0]
