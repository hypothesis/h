# -*- coding: utf-8 -*-
"""Classes for validating data passed to the annotations API."""

import copy
import jsonschema
from jsonschema.exceptions import best_match
from pyramid import i18n

_ = i18n.TranslationStringFactory(__package__)

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


class CreateAnnotationSchema(object):

    """
    Validate the payload from a user when creating an annotation.
    """

    def __init__(self, request):
        self.request = request
        self.structure = AnnotationSchema()

    def validate(self, data):
        appstruct = self.structure.validate(data)

        # Some fields are not to be set by the user, ignore them.
        for field in PROTECTED_FIELDS:
            appstruct.pop(field, None)

        # Set the annotation user field to the request user.
        appstruct['user'] = self.request.authenticated_userid

        # Assert that the user has permission to create an annotation in the
        # group they've asked to create one in.
        if 'group' in appstruct:
            group_principal = 'group:{}'.format(appstruct['group'])
            if group_principal not in self.request.effective_principals:
                raise ValidationError('group: ' +
                                      _('You may not create annotations in '
                                        'groups you are not a member of!'))

        return appstruct


class UpdateAnnotationSchema(object):

    """
    Validate the payload from a user when updating an annotation.
    """

    def __init__(self, request, annotation):
        self.request = request
        self.annotation = annotation
        self.structure = AnnotationSchema()

    def validate(self, data):
        appstruct = self.structure.validate(data)

        # Some fields are not to be set by the user, ignore them.
        for field in PROTECTED_FIELDS:
            appstruct.pop(field, None)

        # The user may not change the permissions of an annotation on which
        # they are lacking 'admin' rights.
        userid = self.request.authenticated_userid
        permissions = self.annotation.get('permissions', {})
        changing_permissions = (
            'permissions' in appstruct and
            appstruct['permissions'] != permissions
        )
        if changing_permissions and userid not in permissions.get('admin', []):
            raise ValidationError('permissions: ' +
                                  _('You may not change the permissions on '
                                    'an annotation unless you have the '
                                    '"admin" permission on that annotation!'))

        # Annotations may not be moved between groups.
        if 'group' in appstruct and 'group' in self.annotation:
            if appstruct['group'] != self.annotation['group']:
                raise ValidationError('group: ' +
                                      _('You may not move annotations between '
                                        'groups!'))

        return appstruct


def _format_jsonschema_error(error):
    """Format a :py:class:`jsonschema.ValidationError` as a string."""
    if error.path:
        dotted_path = '.'.join([str(c) for c in error.path])
        return '{path}: {message}'.format(path=dotted_path,
                                          message=error.message)
    return error.message
