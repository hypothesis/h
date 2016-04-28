# -*- coding: utf-8 -*-
"""Classes for validating data passed to the annotations API."""

import copy
import jsonschema
from jsonschema.exceptions import best_match
from pyramid import i18n
from pyramid import security

from h.api import parse_document_claims

_ = i18n.TranslationStringFactory(__package__)


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

    """Validate an annotation object."""

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
    }

    def __init__(self):
        super(AnnotationSchema, self).__init__()

    def validate(self, data):
        appstruct = super(AnnotationSchema, self).validate(data)
        return appstruct


class LegacyAnnotationSchema(JSONSchema):

    """Validate an annotation object."""

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
        self.structure = AnnotationSchema()
        self.request = request

    def validate(self, data):
        appstruct = self.structure.validate(data)

        new_appstruct = {}

        _remove_protected_fields(appstruct)

        new_appstruct['userid'] = self.request.authenticated_userid
        new_appstruct['target_uri'] = appstruct.pop('uri', u'')
        new_appstruct['text'] = appstruct.pop('text', u'')
        new_appstruct['tags'] = appstruct.pop('tags', [])

        if 'permissions' in appstruct:
            new_appstruct['shared'] = _shared(appstruct.pop('permissions'),
                                              new_appstruct['userid'])
        else:
            new_appstruct['shared'] = True

        if 'target' in appstruct:  # Replies and page notes don't have targets.
            new_appstruct['target_selectors'] = _target_selectors(
                appstruct.pop('target'))

        new_appstruct['groupid'] = appstruct.pop('group', u'__world__')
        new_appstruct['references'] = appstruct.pop('references', [])

        # Replies always get the same groupid as their parent. The parent's
        # groupid is added to the reply annotation later by the storage code.
        # Here we just delete any group sent by the client from replies.
        if new_appstruct['references'] and 'groupid' in new_appstruct:
            del new_appstruct['groupid']

        new_appstruct['document'] = _document(appstruct.pop('document', {}),
                                              new_appstruct['target_uri'])

        new_appstruct['extra'] = appstruct

        return new_appstruct


class LegacyCreateAnnotationSchema(object):

    """Validate the payload from a user when creating an annotation."""

    def __init__(self, request):
        self.request = request
        self.structure = LegacyAnnotationSchema()

    def validate(self, data):
        appstruct = self.structure.validate(data)

        _remove_protected_fields(appstruct)

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
                raise ValidationError('group: ' +
                                      _('You may not create annotations in '
                                        'groups you are not a member of!'))

        return appstruct


class UpdateAnnotationSchema(object):

    """Validate the POSTed data of an update annotation request."""

    def __init__(self, request, existing_target_uri):
        self.request = request
        self.existing_target_uri = existing_target_uri
        self.structure = AnnotationSchema()

    def validate(self, data):
        appstruct = self.structure.validate(data)

        new_appstruct = {}

        _remove_protected_fields(appstruct)

        # Some fields are not allowed to be changed in annotation updates.
        for key in ['group', 'groupid', 'userid', 'references']:
            appstruct.pop(key, '')

        # Fields that are allowed to be updated and that have a different name
        # internally than in the public API.
        if 'uri' in appstruct:
            new_appstruct['target_uri'] = appstruct.pop('uri')

        if 'permissions' in appstruct:
            new_appstruct['shared'] = _shared(
                appstruct.pop('permissions'),
                self.request.authenticated_userid)

        if 'target' in appstruct:
            new_appstruct['target_selectors'] = _target_selectors(
                appstruct.pop('target'))

        # Fields that are allowed to be updated and that have the same internal
        # and external name.
        for key in ['text', 'tags']:
            if key in appstruct:
                new_appstruct[key] = appstruct.pop(key)

        if 'document' in appstruct:
            new_appstruct['document'] = _document(
                appstruct.pop('document'),
                new_appstruct.get('target_uri', self.existing_target_uri))

        # Anything still left in appstruct goes into extra.
        if appstruct:
            new_appstruct['extra'] = appstruct

        return new_appstruct


class LegacyUpdateAnnotationSchema(object):

    """Validate the payload from a user when updating an annotation."""

    def __init__(self, request, annotation):
        self.request = request
        self.annotation = annotation
        self.structure = LegacyAnnotationSchema()

    def validate(self, data):
        appstruct = self.structure.validate(data)

        _remove_protected_fields(appstruct)

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


def _document(document, claimant):
    """
    Return document meta and document URI data from the given document dict.

    Transforms the "document" dict that the client posts into a convenient
    format for creating DocumentURI and DocumentMeta objects later.

    """
    document = document or {}
    document_uri_dicts = parse_document_claims.document_uris_from_data(
        copy.deepcopy(document),
        claimant=claimant)
    document_meta_dicts = parse_document_claims.document_metas_from_data(
        copy.deepcopy(document),
        claimant=claimant)
    return {
        'document_uri_dicts': document_uri_dicts,
        'document_meta_dicts': document_meta_dicts
    }


def _format_jsonschema_error(error):
    """Format a :py:class:`jsonschema.ValidationError` as a string."""
    if error.path:
        dotted_path = '.'.join([str(c) for c in error.path])
        return '{path}: {message}'.format(path=dotted_path,
                                          message=error.message)
    return error.message


def _remove_protected_fields(appstruct):
    # Some fields are not to be set by the user, ignore them.
    for field in ['created', 'updated', 'user', 'id', 'links']:
        appstruct.pop(field, None)


def _shared(permissions, userid):
    """
    Return True if the given permissions object represents shared permissions.

    Return False otherwise.

    Reduces the client's complex permissions dict to a simple shared boolean.

    :param permissions: the permissions dict sent by the client in an
        annotation create or update request
    :type permissions: dict

    :param userid: the userid of the user who created the annotation
    :type userid: unicode

    """
    return permissions['read'] != [userid]


def _target_selectors(targets):
    """
    Return the target selectors from the given target list.

    Transforms the target lists that the client sends in annotation create and
    update requests into our internal target_selectors format.

    """
    # Any targets other than the first in the list are discarded.
    # Any fields of the target other than 'selector' are discarded.
    if targets:
        return targets[0]['selector']
    else:
        return []
