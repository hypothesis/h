# -*- coding: utf-8 -*-
"""Classes for validating data passed to the annotations API."""

import copy
import jsonschema
from jsonschema.exceptions import best_match


# These annotation fields are not to be set by the user.
PROTECTED_FIELDS = ['created', 'updated', 'user', 'id']


class ValidationError(Exception):
    pass


class JSONSchema(object):

    """
    Validate data according to a Draft 4 JSON Schema.

    Inherit from this class and override the `schema` class property with a
    valid JSON schema.
    """

    schema = {}

    def __init__(self):
        self.validator = jsonschema.Draft4Validator(self.schema)

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


class AnnotationSchema(JSONSchema):

    """
    Validate an annotation object.
    """

    schema = {
        'type': 'object',
        'properties': {
            'document': {
                'type': 'object',
                'properties': {
                    'link': {
                        'type': 'array',
                    },
                },
            },
            'permissions': {
                'title': 'Permissions',
                'description': 'Annotation action access control list',
                'type': 'object',
                'patternProperties': {
                    '^(admin|delete|read|update)$': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'pattern': '^(acct:|group:).+$',
                        },
                    }
                },
            },
        },
    }

    def validate(self, data):
        appstruct = super(AnnotationSchema, self).validate(data)

        # Some fields are not to be set by the user, ignore them
        for field in PROTECTED_FIELDS:
            appstruct.pop(field, None)

        return appstruct


def _format_jsonschema_error(error):
    """Format a :py:class:`jsonschema.ValidationError` as a string."""
    if error.path:
        dotted_path = '.'.join([str(c) for c in error.path])
        return '{path}: {message}'.format(path=dotted_path,
                                          message=error.message)
    return error.message
