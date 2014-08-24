# -*- coding: utf-8 -*-
from ..interfaces import IConsumerClass


def is_browser_client(request, client_id):  # pragma: no cover
    return client_id == request.registry.settings['api.key']


try:
    # pylint: disable=no-name-in-module
    from hmac import compare_digest as is_equal
except ImportError:
    def is_equal(lhs, rhs):
        """Returns True if the two strings are equal, False otherwise.

        The comparison is based on a common implementation found in Django.
        This version avoids a short-circuit even for unequal lengths to reveal
        as little as possible. It takes time proportional to the length of its
        second argument.
        """
        result = 0 if len(lhs) == len(rhs) else 1
        lhs = lhs.ljust(len(rhs))
        for x, y in zip(lhs, rhs):
            result |= ord(x) ^ ord(y)
        return result == 0


def get_consumer(request, client_id=None):
    registry = request.registry
    settings = registry.settings

    key = client_id or settings['api.key']
    consumer_ctor = registry.getUtility(IConsumerClass)

    if key == settings['api.key'] and 'api.secret' in settings:
        consumer = consumer_ctor(key=key, secret=settings['api.secret'])
    else:
        consumer = consumer_ctor.get_by_key(request, key)

    return consumer
