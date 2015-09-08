# -*- coding: utf-8 -*-
from __future__ import absolute_import

import hashids

# Global shared salt. This is initialized at application boot time.
SALT = None


class NotInitializedError(Exception):
    pass


def serializer(salt, context):
    if salt is None:
        raise NotInitializedError('Salt not set! Has the application booted?')
    return hashids.Hashids(salt=salt + context, min_length=6)


def encode(context, *values):
    """Return a hashid of the given values."""
    return serializer(SALT, context).encode(*values)


def decode(context, hashid):
    """Decode the given hashid and return the original encoded value."""
    return serializer(SALT, context).decode(str(hashid))


def decode_one(context, hashid):
    """Decode the given hashid and return the single encoded value."""
    value = decode(context, hashid)
    if len(value) != 1:
        return None
    return value[0]


def _set_salt(registry):
    global SALT
    SALT = registry.settings.get('h.hashids.salt')


def includeme(config):
    # When the configuration is committed, set the global shared salt.
    config.action(None, _set_salt, (config.registry,))
