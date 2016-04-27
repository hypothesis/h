# -*- coding: utf-8 -*-
"""Classes for validating data passed to the annotations API."""

import copy
import functools

import jsonschema
from jsonschema.exceptions import best_match
from pyramid import i18n
from pyramid import security

from h.api import checkers
from h.api import exceptions
from h.api import parse_document_claims

_ = i18n.TranslationStringFactory(__package__)

# These annotation fields are not to be set by the user.
PROTECTED_FIELDS = ['created', 'updated', 'user', 'id']


class JSONSchema(object):

    """
    Validate data according to a Draft 4 JSON Schema.

    Inherit from this class and override the `schema` class property with a
    valid JSON schema.
    """

    schema = {}

    def __init__(self, format_checker=None):
        self.validator = jsonschema.Draft4Validator(self.schema, format_checker=format_checker)

    def validate(self, data):
        """
        Validate `data` according to the current schema.

        :param data: The data to be validated
        :return: valid data
        :raises h.api.exceptions.ValidationError: if the data is invalid
        """
        # Take a copy to ensure we don't modify what we were passed.
        appstruct = copy.deepcopy(data)
        error = best_match(self.validator.iter_errors(appstruct))
        if error is not None:
            raise exceptions.ValidationError(_format_jsonschema_error(error))
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
                    'dc': {
                        'type': 'object',
                        'properties': {
                            'identifier': {
                                'type': 'array',
                                'items': {
                                    'type': 'string',
                                },
                            },
                        },
                    },
                    'highwire': {
                        'type': 'object',
                        'properties': {
                            'doi': {
                                'type': 'array',
                                'items': {
                                    'type': 'string',
                                },
                            },
                        },
                    },
                    'link': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'href': {
                                    'type': 'string',
                                },
                                'type': {
                                    'type': 'string',
                                },
                            },
                            'required': [
                                'href',
                            ],
                        },
                    },
                },
            },
            'group': {
                'type': 'string',
                'format': 'group_permissions',
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
                'required': [
                    'read',
                ],
            },
            'references': {
                'type': 'array',
                'items': {
                    'type': 'string',
                },
            },
            'tags': {
                'type': 'array',
                'items': {
                    'type': 'string',
                },
            },
            'target': {
                'type': 'array',
                'items': [
                    {
                        'type': 'object',
                        'properties': {
                            'selector': {
                            },
                        },
                        'required': [
                            'selector',
                        ],
                    },
                ],
            },
            'text': {
                'type': 'string',
            },
            'uri': {
                'type': 'string',
            },
        },
        'required': [
            'permissions',
        ],
    }

    def __init__(self, request, format_checker=None):
        super(AnnotationSchema, self).__init__(format_checker=format_checker)
        self.request = request

    def validate(self, data):
        appstruct = super(AnnotationSchema, self).validate(data)

        new_appstruct = {}

        # Some fields are not to be set by the user, ignore them.
        for field in PROTECTED_FIELDS:
            appstruct.pop(field, None)

        new_appstruct['userid'] = self.request.authenticated_userid
        new_appstruct['target_uri'] = appstruct.pop('uri', u'')
        new_appstruct['text'] = appstruct.pop('text', u'')
        new_appstruct['tags'] = appstruct.pop('tags', [])

        # Replace the client's complex permissions object with a simple shared
        # boolean.
        if appstruct.pop('permissions')['read'] == [new_appstruct['userid']]:
            new_appstruct['shared'] = False
        else:
            new_appstruct['shared'] = True

        # The 'target' dict that the client sends is replaced with a single
        # annotation.target_selectors whose value is the first selector in
        # the client'ss target.selectors list.
        # Anything else in the target dict, and any selectors after the first,
        # are discarded.
        target = appstruct.pop('target', [])
        if target:  # Replies and page notes don't have 'target'.
            target = target[0]  # Multiple targets are ignored.
            new_appstruct['target_selectors'] = target['selector']

        new_appstruct['groupid'] = appstruct.pop('group', u'__world__')
        new_appstruct['references'] = appstruct.pop('references', [])

        # Replies always get the same groupid as their parent. The parent's
        # groupid is added to the reply annotation later by the storage code.
        # Here we just delete any group sent by the client from replies.
        if new_appstruct['references'] and 'groupid' in new_appstruct:
            del new_appstruct['groupid']

        new_appstruct['extra'] = appstruct

        # Transform the "document" dict that the client posts into a convenient
        # format for creating DocumentURI and DocumentMeta objects later.
        document_data = appstruct.pop('document', {})
        document_uri_dicts = parse_document_claims.document_uris_from_data(
            copy.deepcopy(document_data),
            claimant=new_appstruct['target_uri'])
        document_meta_dicts = parse_document_claims.document_metas_from_data(
            copy.deepcopy(document_data),
            claimant=new_appstruct['target_uri'])
        new_appstruct['document'] = {
            'document_uri_dicts': document_uri_dicts,
            'document_meta_dicts': document_meta_dicts
        }

        return new_appstruct


class LegacyAnnotationSchema(JSONSchema):

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

    """Validate the POSTed data of a create annotation request."""

    def __init__(self, request):
        checker = jsonschema.FormatChecker()
        checker.checks('group_permissions')(
            functools.partial(
                checkers.check_group_permissions,
                request.effective_principals
            )
        )
        self.structure = AnnotationSchema(request, format_checker=checker)

    def validate(self, data):
        return self.structure.validate(data)


class LegacyCreateAnnotationSchema(object):

    """
    Validate the payload from a user when creating an annotation.
    """

    def __init__(self, request):
        self.request = request
        self.structure = LegacyAnnotationSchema()

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
            if appstruct['group'] == '__world__':
                group_principal = security.Everyone
            else:
                group_principal = 'group:{}'.format(appstruct['group'])
            if group_principal not in self.request.effective_principals:
                raise exceptions.ValidationError(
                    'group: ' + _('You may not create annotations in groups '
                                  'you are not a member of!'))

        return appstruct


class UpdateAnnotationSchema(object):

    """Validate the POSTed data of an update annotation request."""

    def __init__(self, request, annotation):
        self.request = request
        self.annotation = annotation
        self.structure = AnnotationSchema(request)

    def validate(self, data):
        appstruct = self.structure.validate(data)

        if appstruct['groupid'] != self.annotation.groupid:
            raise exceptions.ValidationError(
                'group: ' + _("You can't move annotations between groups"))

        return appstruct



class LegacyUpdateAnnotationSchema(object):

    """
    Validate the payload from a user when updating an annotation.
    """

    def __init__(self, request, annotation):
        self.request = request
        self.annotation = annotation
        self.structure = LegacyAnnotationSchema()

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
            raise exceptions.ValidationError(
                'permissions: ' + _('You may not change the permissions on '
                                    'an annotation unless you have the '
                                    '"admin" permission on that annotation!'))

        # Annotations may not be moved between groups.
        if 'group' in appstruct and 'group' in self.annotation:
            if appstruct['group'] != self.annotation['group']:
                raise exceptions.ValidationError(
                    'group: ' + _('You may not move annotations between '
                                  'groups!'))

        return appstruct


def _format_jsonschema_error(error):
    """Format a :py:class:`jsonschema.ValidationError` as a string."""
    if error.path:
        dotted_path = '.'.join([str(c) for c in error.path])
        return '{path}: {message}'.format(path=dotted_path,
                                          message=error.message)
    return error.message
