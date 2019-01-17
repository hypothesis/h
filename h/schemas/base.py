# -*- coding: utf-8 -*-

"""Shared functionality for schemas."""

from __future__ import unicode_literals

import copy

import colander
import deform
import jsonschema
from pyramid.session import check_csrf_token
from pyramid import httpexceptions


@colander.deferred
def deferred_csrf_token(node, kw):
    request = kw.get("request")
    return request.session.get_csrf_token()


class ValidationError(httpexceptions.HTTPBadRequest):
    pass


class CSRFSchema(colander.Schema):
    """
    A CSRFSchema backward-compatible with the one from the hem module.

    Unlike hem, this doesn't require that the csrf_token appear in the
    serialized appstruct.
    """

    csrf_token = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.HiddenWidget(),
        default=deferred_csrf_token,
        missing=None,
    )

    def validator(self, form, value):
        request = form.bindings["request"]
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
        self.validator = jsonschema.Draft4Validator(
            self.schema, format_checker=format_checker
        )

    def validate(self, data):
        """
        Validate `data` according to the current schema.

        :param data: The data to be validated
        :returns: valid data
        :raises ~h.schemas.ValidationError: if the data is invalid
        """
        # Take a copy to ensure we don't modify what we were passed.
        appstruct = copy.deepcopy(data)

        errors = list(self.validator.iter_errors(appstruct))
        if errors:
            msg = ", ".join([_format_jsonschema_error(e) for e in errors])
            raise ValidationError(msg)
        return appstruct


def enum_type(enum_cls):
    """
    Return a `colander.Type` implementation for a field with a given enum type.

    :param enum_cls: The enum class
    :type enum_cls: enum.Enum
    """

    class EnumType(colander.SchemaType):
        def deserialize(self, node, cstruct):
            if cstruct == colander.null:
                return None

            try:
                return enum_cls[cstruct]
            except KeyError:
                msg = '"{}" is not a known value'.format(cstruct)
                raise colander.Invalid(node, msg)

        def serialize(self, node, appstruct):
            if not appstruct:
                return ""
            return appstruct.name

    return EnumType


def _format_jsonschema_error(error):
    """Format a :py:class:`jsonschema.ValidationError` as a string."""
    if error.path:
        dotted_path = ".".join([str(c) for c in error.path])
        return "{path}: {message}".format(path=dotted_path, message=error.message)
    return error.message
