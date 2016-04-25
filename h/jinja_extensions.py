# -*- coding: utf-8 -*-
from functools import wraps

import datetime
import json

from jinja2 import Markup
from jinja2.ext import Extension


class Filters(Extension):

    """
    Set up filters for Jinja2.
    """

    def __init__(self, environment):
        super(Filters, self).__init__(environment)

        environment.filters['human_timestamp'] = human_timestamp
        environment.filters['to_json'] = to_json


class IncludeRawExtension(Extension):
    """
    An extension which provides a simple include_raw function to include the
    content of a file without further processing.
    """

    def __init__(self, environment):
        super(IncludeRawExtension, self).__init__(environment)

        environment.globals['include_raw'] = _get_includer(environment)


def human_timestamp(timestamp, now=datetime.datetime.utcnow):
    """Turn a :py:class:`datetime.datetime` into a human-friendly string."""
    fmt = '%d %B at %H:%M'
    if timestamp.year < now().year:
        fmt = '%d %B %Y at %H:%M'
    return timestamp.strftime(fmt)


def to_json(value):
    """Convert a dict into a JSON string"""
    return Markup(json.dumps(value))


def _get_includer(environment):
    def _include(name):
        return Markup(environment.loader.get_source(environment, name)[0])
    # Memoize results when [jinja2.]debug_templates is false.
    if not environment.loader.debug:
        _include = _memoize(_include)
    return _include


def _memoize(f):
    cache = {}

    @wraps(f)
    def memoizer(*args, **kwargs):
        # NB: this memoizer ignores kwargs.
        if args not in cache:
            cache[args] = f(*args, **kwargs)
        return cache[args]
    return memoizer
