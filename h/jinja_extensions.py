# -*- coding: utf-8 -*-
from functools import wraps

from jinja2 import Markup
from jinja2.ext import Extension


class IncludeRawExtension(Extension):
    """
    An extension which provides a simple include_raw function to include the
    content of a file without further processing.
    """

    def __init__(self, environment):
        super(IncludeRawExtension, self).__init__(environment)

        environment.globals['include_raw'] = _get_includer(environment)


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
