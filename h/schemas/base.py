# -*- coding: utf-8 -*-

"""Shared functionality for schemas."""

from __future__ import unicode_literals

import copy

import colander
import deform
import jsonschema
from jsonschema.exceptions import best_match
from pyramid.session import check_csrf_token


@colander.deferred
def deferred_csrf_token(node, kw):
    request = kw.get('request')
    return request.session.get_csrf_token()


class ValidationError(Exception):
    pass


class CSRFSchema(colander.Schema):
    """
    A CSRFSchema backward-compatible with the one from the hem module.

    Unlike hem, this doesn't require that the csrf_token appear in the
    serialized appstruct.
    """

    csrf_token = colander.SchemaNode(colander.String(),
                                     widget=deform.widget.HiddenWidget(),
                                     default=deferred_csrf_token,
                                     missing=None)

    def validator(self, form, value):
        request = form.bindings['request']
        check_csrf_token(request)


class JSONSchema(object):
    """
    Validate data according to a Draft 4 JSON Schema.

    Inherit from this class and override the `schema` class property with a
    valid JSON schema.
    """

    schema = {}

    def __init__(self):
        format_checker = jsonschema.FormatChecker()
        self.validator = jsonschema.Draft4Validator(self.schema,
                                                    format_checker=format_checker)

    def validate(self, data):
        """
        Validate `data` according to the current schema.

        :param data: The data to be validated
        :return: valid data
        :raises ValidationError: if the data is invalid
        """
        # Take a copy to ensure we don't modify what we were passed.
        appstruct = copy.deepcopy(data)
        error = best_match(self.validator.iter_errors(appstruct))
        if error is not None:
            raise ValidationError(_format_jsonschema_error(error))
        return appstruct


def _format_jsonschema_error(error):
    """Format a :py:class:`jsonschema.ValidationError` as a string."""
    if error.path:
        dotted_path = '.'.join([str(c) for c in error.path])
        return '{path}: {message}'.format(path=dotted_path,
                                          message=error.message)
    return error.message
