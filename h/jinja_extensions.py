# -*- coding: utf-8 -*-

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

        environment.filters['to_json'] = to_json


def to_json(value):
    """Convert a dict into a JSON string"""
    return Markup(json.dumps(value))
