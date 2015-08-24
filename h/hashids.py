# -*- coding: utf-8 -*-
from __future__ import absolute_import

from pyramid import exceptions

import hashids


class SimplerHashids(object):

    """A simple wrapper class for hashids.Hashids.

    Simplifies the interface slightly and adds the "context" argument.

    """

    def __init__(self, salt):
        self.salt = salt

    def _get_hashids(self, context):
        return hashids.Hashids(salt=self.salt + context, min_length=6)

    def encode(self, context, number):
        """Return a hashid of the given number."""
        return self._get_hashids(context).encode(number)

    def decode(self, context, hashid):
        """Decode the given hashid and return the original number."""
        return self._get_hashids(context).decode(str(hashid))[0]


def includeme(config):
    salt = config.registry.settings.get("h.hashids.salt")

    if not salt:
        raise exceptions.ConfigurationError(
            "There needs to be a h.hashids.salt config setting")

    # Add a request.hashids object.
    #
    # Usage:
    #
    #     hashid = request.hashids.encode(context, number)
    #     number = request.hashids.decode(context, hashid)
    config.add_request_method(
        lambda request: SimplerHashids(salt), 'hashids', reify=True)
